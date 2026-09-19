from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

from agentnative.acquisition.fetcher import AcquisitionError, FixtureFetcher, SafeFetcher
from agentnative.models import Artifact, ArtifactStatus, DiscoveredSurface, Limitation
from agentnative.parsers.html import parse_html
from agentnative.parsers.openapi import OpenAPIParseError, parse_openapi


COMMON_ARTIFACTS = (
    "/openapi.json",
    "/swagger.json",
    "/api/openapi.json",
    "/.well-known/agent-card.json",
    "/.well-known/agent.json",
    "/robots.txt",
)


def discover(target: str, fetcher: SafeFetcher | None = None) -> DiscoveredSurface:
    path = Path(target)
    fetcher = fetcher or (FixtureFetcher() if path.exists() else SafeFetcher())
    surface = DiscoveredSurface()
    if path.exists():
        if not isinstance(fetcher, FixtureFetcher):
            raise AcquisitionError("local fixture discovery requires the separate FixtureFetcher")
        _discover_local(path, surface, fetcher)
        return surface
    root = fetcher.fetch(target)
    surface.artifacts.append(root)
    _parse_artifact(root, surface)
    root_url = root.uri
    candidates = _candidate_urls(root_url, surface)
    for candidate in candidates:
        try:
            artifact = fetcher.fetch(candidate)
        except (AcquisitionError, ValueError) as exc:
            message = f"Could not acquire {candidate}: {exc}"
            surface.limitations.append(Limitation("DISCOVERY_FETCH_FAILED", candidate, type(exc).__name__))
            surface.artifacts.append(SafeFetcher.acquisition_error_artifact(candidate, message))
            continue
        surface.artifacts.append(artifact)
        _parse_artifact(artifact, surface)
    return surface


def _discover_local(path: Path, surface: DiscoveredSurface, fetcher: SafeFetcher) -> None:
    files = [path] if path.is_file() else [path / "index.html", path / "openapi.json", path / "agent-card.json", path / "robots.txt"]
    for candidate in files:
        if not candidate.exists() or not candidate.is_file():
            continue
        artifact = fetcher.fetch_file(candidate)
        surface.artifacts.append(artifact)
        _parse_artifact(artifact, surface)
    if not surface.artifacts:
        surface.limitations.append(Limitation("LOCAL_ARTIFACTS_NOT_FOUND", str(path), "No supported local artifacts found"))


def _candidate_urls(root_url: str, surface: DiscoveredSurface) -> list[str]:
    parsed_root = urlparse(root_url)
    candidates: list[str] = []
    for link in surface.identity.get("_links", []) if isinstance(surface.identity, dict) else []:
        candidate = urljoin(root_url, link)
        parsed = urlparse(candidate)
        if parsed.netloc == parsed_root.netloc and parsed.scheme == parsed_root.scheme:
            candidates.append(candidate)
    for suffix in COMMON_ARTIFACTS:
        candidates.append(urljoin(root_url, suffix))
    return list(dict.fromkeys(candidates))


def _parse_artifact(artifact: Artifact, surface: DiscoveredSurface) -> None:
    suffix = Path(urlparse(artifact.uri).path).suffix.lower()
    content_type = (artifact.media_type or "").lower()
    if suffix in {".html", ".htm"} or "html" in content_type or artifact.uri.endswith("/"):
        parsed = parse_html(artifact.content)
        surface.identity.setdefault("_links", []).extend(parsed["links"])
        surface.identity.setdefault("title", parsed["title"])
        surface.identity.setdefault("metas", []).extend(parsed["metas"])
        surface.structured_metadata.extend(parsed["json_ld"])
        for item in parsed["json_ld"]:
            if any(key in item for key in ("agentProtocol", "agentCard", "capabilities", "tools")):
                surface.agent_metadata.append(item)
        artifact.parse_status = ArtifactStatus.PARSED
        return
    is_json_candidate = suffix in {".json", ".map"} or "json" in content_type or any(marker in artifact.uri.lower() for marker in ("openapi", "swagger", "agent-card", "agent.json"))
    if not is_json_candidate:
        artifact.parse_status = ArtifactStatus.PARSED
        return
    try:
        parsed_json = json.loads(artifact.content)
    except json.JSONDecodeError:
        _parse_error(artifact, surface, "invalid JSON")
        return
    if not isinstance(parsed_json, dict):
        _parse_error(artifact, surface, "JSON artifact is not an object")
        return
    if isinstance(parsed_json, dict) and (parsed_json.get("openapi") or parsed_json.get("swagger")):
        try:
            surface.openapi.append(parse_openapi(artifact.content, artifact.uri))
            artifact.parse_status = ArtifactStatus.PARSED
        except OpenAPIParseError as exc:
            _parse_error(artifact, surface, str(exc))
    elif any(marker in artifact.uri.lower() for marker in ("openapi", "swagger")):
        _parse_error(artifact, surface, "JSON artifact does not declare OpenAPI or Swagger")
    elif isinstance(parsed_json, dict) and any(key in parsed_json for key in ("agentProtocol", "agentCard", "capabilities", "tools")):
        surface.agent_metadata.append(parsed_json)
        artifact.parse_status = ArtifactStatus.PARSED
    elif isinstance(parsed_json, dict):
        surface.structured_metadata.append(parsed_json)
        artifact.parse_status = ArtifactStatus.PARSED


def _parse_error(artifact: Artifact, surface: DiscoveredSurface, message: str) -> None:
    artifact.parse_status = ArtifactStatus.PARSE_ERROR
    artifact.error = message[:300]
    surface.limitations.append(Limitation("ARTIFACT_PARSE_FAILURE", artifact.uri, f"Artifact parse failure: {artifact.error}"))

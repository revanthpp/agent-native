from __future__ import annotations

import copy
import ipaddress
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urljoin, urlsplit

from agentnative.acquisition.fetcher import SafeFetcher
from agentnative.protocols.models import Limitation, ProtocolArtifact


@dataclass(frozen=True)
class RemoteArtifact:
    uri: str
    content: str | bytes | dict[str, Any]
    content_hash: str | None = None
    final_uri: str | None = None


class SafeRefResolver:
    """Bounded local and same-origin HTTPS `$ref` resolver.

    A caller may inject a deterministic fetch function for tests. Production
    parsing defaults to :class:`SafeFetcher`, so remote references use the same
    HTTPS, DNS-rebinding, redirect, request, and response-size policy as the
    rest of acquisition.
    """

    def __init__(self, root: dict[str, Any], root_uri: str, fetch: Callable[[str], RemoteArtifact] | None = None, *, max_depth: int = 16, max_documents: int = 100, enforce_network_policy: bool = True) -> None:
        self.root, self.root_uri = root, root_uri
        self.enforce_network_policy = enforce_network_policy
        try:
            root_scheme = urlsplit(root_uri).scheme
        except ValueError:
            root_scheme = ""
        self._safe_fetcher = SafeFetcher() if fetch is None and root_scheme == "https" else None
        self.fetch = fetch or (self._fetch_with_safe_policy if self._safe_fetcher is not None else None)
        self.max_depth, self.max_documents, self.document_count = max_depth, max_documents, 0
        self.limitations: list[Limitation] = []; self.artifacts: list[ProtocolArtifact] = []; self._documents = {root_uri: root}; self._document_bases = {root_uri: root_uri}

    @staticmethod
    def _origin(uri: str) -> tuple[str, str, int | None]:
        try:
            parsed = urlsplit(uri)
            port = parsed.port
        except ValueError:
            return "", "", None
        if port is None and parsed.scheme in {"https", "http"}: port = 443 if parsed.scheme == "https" else 80
        return parsed.scheme.lower(), (parsed.hostname or "").lower().rstrip("."), port

    def _fetch_with_safe_policy(self, uri: str) -> RemoteArtifact:
        assert self._safe_fetcher is not None
        artifact = self._safe_fetcher.fetch(uri)
        return RemoteArtifact(artifact.uri, artifact.content, artifact.content_hash, artifact.uri)

    @staticmethod
    def _blocked(uri: str) -> str | None:
        try:
            parsed = urlsplit(uri)
            _ = parsed.port
        except ValueError:
            return "OAS_REF_INVALID_URI"
        if parsed.scheme not in {"http", "https"}: return "OAS_REF_UNSUPPORTED_SCHEME"
        if not parsed.hostname: return "OAS_REF_INVALID_URI"
        try: unsafe = not ipaddress.ip_address(parsed.hostname).is_global
        except ValueError: unsafe = parsed.hostname.lower() in {"localhost", "metadata", "metadata.google.internal"}
        if unsafe: return "OAS_REF_PRIVATE_NETWORK"
        return None if parsed.scheme == "https" else "OAS_REF_UNSUPPORTED_SCHEME"

    def resolve(self, value: Any, *, document_uri: str | None = None, depth: int = 0, stack: tuple[str, ...] = (), pointer: str = "") -> Any:
        if depth > self.max_depth: self.limitations.append(Limitation("OAS_REF_DEPTH", "maximum $ref depth exceeded", pointer)); return value
        if isinstance(value, list): return [self.resolve(item, document_uri=document_uri, depth=depth, stack=stack, pointer=f"{pointer}/{i}") for i, item in enumerate(value)]
        if not isinstance(value, dict): return value
        ref = value.get("$ref")
        if not isinstance(ref, str): return {key: self.resolve(item, document_uri=document_uri, depth=depth, stack=stack, pointer=f"{pointer}/{key}") for key, item in value.items()}
        base = document_uri or self.root_uri
        absolute, fragment = (ref.split("#", 1) + [""])[:2] if "#" in ref else (ref, "")
        target_uri = urljoin(base, absolute) if absolute else base
        if target_uri != base:
            if self.enforce_network_policy:
                blocked = self._blocked(target_uri)
                if blocked: self.limitations.append(Limitation(blocked, "remote reference blocked by network policy", target_uri)); return value
                if self._origin(target_uri) != self._origin(self.root_uri): self.limitations.append(Limitation("OAS_REF_CROSS_ORIGIN", "cross-origin remote references are not enabled", target_uri)); return value
            if self.fetch is None: self.limitations.append(Limitation("OAS_REF_REMOTE_UNAVAILABLE", "safe remote fetcher was not configured", target_uri)); return value
            if target_uri not in self._documents:
                self.document_count += 1
                if self.document_count > self.max_documents: self.limitations.append(Limitation("OAS_REF_DOCUMENT_COUNT", "maximum referenced document count exceeded", target_uri)); return value
                try:
                    artifact = self.fetch(target_uri)
                except Exception as exc:
                    self.limitations.append(Limitation("OAS_REF_FETCH_FAILED", f"referenced document could not be acquired: {type(exc).__name__}", target_uri)); return value
                final_uri = artifact.final_uri or artifact.uri
                if self.enforce_network_policy and (self._blocked(final_uri) or self._origin(final_uri) != self._origin(self.root_uri)):
                    self.limitations.append(Limitation("OAS_REF_REDIRECT_BLOCKED", "remote reference redirect failed origin/network revalidation", final_uri)); return value
                from agentnative.protocols.openapi.parser import load_openapi_document
                try:
                    self._documents[target_uri] = load_openapi_document(artifact.content)
                except (TypeError, ValueError):
                    self.limitations.append(Limitation("OAS_REF_PARSE_FAILED", "referenced document was not a valid JSON/YAML object", target_uri)); return value
                self._document_bases[target_uri] = final_uri; self.artifacts.append(ProtocolArtifact(final_uri, "openapi-ref", artifact.content_hash))
        document = self._documents.get(target_uri)
        if document is None: self.limitations.append(Limitation("OAS_REF_MISSING", "referenced document was not available", target_uri)); return value
        key = target_uri + "#" + fragment
        if key in stack: self.limitations.append(Limitation("OAS_REF_CYCLE", "recursive reference cycle detected", key)); return value
        target: Any = document
        try:
            for part in fragment.lstrip("/").split("/") if fragment else []: target = target[part.replace("~1", "/").replace("~0", "~")]
        except (KeyError, TypeError): self.limitations.append(Limitation("OAS_REF_MISSING", "referenced pointer does not exist", key)); return value
        return self.resolve(copy.deepcopy(target), document_uri=self._document_bases.get(target_uri, target_uri), depth=depth + 1, stack=stack + (key,), pointer=key)

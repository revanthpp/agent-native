from __future__ import annotations

import hashlib
import socket
import ssl
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

from agentnative.models import Artifact, ArtifactStatus, utc_now
from agentnative.security.policy import NetworkPolicy, UnsafeTargetError, resolve_public_addresses, validate_network_url


class AcquisitionError(RuntimeError):
    pass


@dataclass
class Response:
    uri: str
    status_code: int
    headers: dict[str, str]
    body: bytes


class SafeFetcher:
    def __init__(self, policy: NetworkPolicy | None = None) -> None:
        self.policy = policy or NetworkPolicy()
        self.request_count = 0
        self.redirect_count = 0

    def fetch(self, url: str) -> Artifact:
        return self._fetch_url(url)

    @staticmethod
    def acquisition_error_artifact(uri: str, message: str) -> Artifact:
        return Artifact(
            uri=uri,
            artifact_type="network",
            content="",
            content_hash="",
            acquisition_timestamp=utc_now(),
            status_code=None,
            error=message,
            parse_status=ArtifactStatus.ACQUISITION_ERROR,
        )

    def _fetch_url(self, url: str) -> Artifact:
        current = validate_network_url(url, self.policy)
        while True:
            if self.request_count >= self.policy.max_requests:
                raise AcquisitionError("request budget exhausted")
            response = self._request_once(current)
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location:
                    raise AcquisitionError("redirect response did not include a location")
                self.redirect_count += 1
                if self.redirect_count > self.policy.max_redirects:
                    raise AcquisitionError("redirect limit exceeded")
                current = validate_network_url(urljoin(current, location), self.policy)
                continue
            if response.status_code >= 400:
                raise AcquisitionError(f"target returned HTTP {response.status_code}")
            media_type = response.headers.get("content-type", "").split(";", 1)[0].strip() or None
            return self._artifact(current, response.body, "http", media_type, response.status_code, response.headers)

    def _request_once(self, url: str) -> Response:
        parsed = urlparse(url)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        addresses = resolve_public_addresses(
            parsed.hostname or "",
            port,
            allow_loopback=parsed.scheme == "http" and self.policy.allow_local_http,
        )
        last_error: OSError | None = None
        for address in addresses:
            try:
                sock = socket.create_connection((address, port), timeout=self.policy.timeout_seconds)
                sock.settimeout(self.policy.timeout_seconds)
                if parsed.scheme == "https":
                    context = ssl.create_default_context()
                    sock = context.wrap_socket(sock, server_hostname=parsed.hostname)
                request_target = parsed.path or "/"
                if parsed.query:
                    request_target += "?" + parsed.query
                host_header = parsed.hostname or ""
                if parsed.port:
                    host_header += f":{parsed.port}"
                request = (
                    f"GET {request_target} HTTP/1.1\r\n"
                    f"Host: {host_header}\r\n"
                    f"User-Agent: {self.policy.user_agent}\r\n"
                    "Accept: text/html,application/json,application/yaml,text/plain;q=0.8\r\n"
                    "Accept-Encoding: identity\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("ascii", "strict")
                sock.sendall(request)
                raw = bytearray()
                while True:
                    chunk = sock.recv(min(65536, self.policy.max_response_bytes + 1 - len(raw)))
                    if not chunk:
                        break
                    raw.extend(chunk)
                    if len(raw) > self.policy.max_response_bytes + 8192:
                        raise AcquisitionError("response exceeds size limit")
                sock.close()
                head, separator, body = bytes(raw).partition(b"\r\n\r\n")
                if not separator:
                    raise AcquisitionError("malformed HTTP response")
                lines = head.split(b"\r\n")
                status_line = lines[0].decode("latin-1")
                status_code = int(status_line.split(" ", 2)[1])
                headers: dict[str, str] = {}
                for line in lines[1:]:
                    if b":" not in line:
                        continue
                    key, value = line.split(b":", 1)
                    headers[key.decode("latin-1").lower()] = value.decode("latin-1").strip()
                if len(body) > self.policy.max_response_bytes:
                    raise AcquisitionError("response exceeds size limit")
                self.request_count += 1
                return Response(url, status_code, headers, body)
            except (OSError, ssl.SSLError) as exc:
                last_error = exc
                continue
        raise AcquisitionError(f"connection failed: {last_error}")

    @staticmethod
    def _artifact(uri: str, data: bytes, artifact_type: str, media_type: str | None, status_code: int | None, headers: dict[str, str]) -> Artifact:
        return Artifact(
            uri=uri,
            artifact_type=artifact_type,
            content=data.decode("utf-8", errors="replace"),
            content_hash=hashlib.sha256(data).hexdigest(),
            acquisition_timestamp=utc_now(),
            media_type=media_type,
            status_code=status_code,
            headers={str(key).lower(): str(value) for key, value in headers.items()},
            parse_status=ArtifactStatus.ACQUIRED,
        )


class FixtureFetcher:
    """Local fixture acquisition used only by explicit local fixture inputs."""

    def __init__(self, max_response_bytes: int = 1_000_000) -> None:
        self.max_response_bytes = max_response_bytes

    def fetch(self, url: str) -> Artifact:
        raise UnsafeTargetError("FixtureFetcher accepts local paths, not network URLs")

    def fetch_file(self, path: Path, uri: str | None = None) -> Artifact:
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise AcquisitionError(f"could not read local artifact: {path}") from exc
        if len(data) > self.max_response_bytes:
            raise AcquisitionError("local artifact exceeds response size limit")
        artifact_uri = uri or path.resolve().as_uri()
        return Artifact(
            uri=artifact_uri,
            artifact_type="local_file",
            content=data.decode("utf-8", errors="replace"),
            content_hash=hashlib.sha256(data).hexdigest(),
            acquisition_timestamp=utc_now(),
            media_type="application/octet-stream",
            status_code=200,
            parse_status=ArtifactStatus.ACQUIRED,
        )

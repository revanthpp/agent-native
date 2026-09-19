from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse


class UnsafeTargetError(ValueError):
    """Raised when a target violates the outbound network policy."""


@dataclass(frozen=True)
class NetworkPolicy:
    allow_local_http: bool = False
    max_redirects: int = 3
    max_requests: int = 8
    max_response_bytes: int = 1_000_000
    timeout_seconds: float = 5.0
    user_agent: str = "AgentNative/0.1 (+https://github.com/agent-native/agent-native)"


def _is_unsafe_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return any(
        (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
            getattr(ip, "is_site_local", False),
        )
    )


def resolve_public_addresses(hostname: str, port: int, *, allow_loopback: bool = False) -> list[str]:
    try:
        infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise UnsafeTargetError(f"hostname could not be resolved: {hostname}") from exc
    addresses = sorted({info[4][0] for info in infos})
    if not addresses:
        raise UnsafeTargetError(f"hostname has no usable address: {hostname}")
    unsafe = [
        address
        for address in addresses
        if _is_unsafe_ip(address) and not (allow_loopback and ipaddress.ip_address(address).is_loopback)
    ]
    if unsafe:
        raise UnsafeTargetError(f"target resolves to a private or reserved address: {unsafe[0]}")
    return addresses


def validate_network_url(value: str, policy: NetworkPolicy) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"https", "http"}:
        raise UnsafeTargetError("only http and https targets are supported")
    if parsed.username or parsed.password:
        raise UnsafeTargetError("credentials embedded in target URLs are not allowed")
    if not parsed.hostname:
        raise UnsafeTargetError("target URL must include a hostname")
    if parsed.scheme == "http" and not policy.allow_local_http:
        raise UnsafeTargetError("http is disabled; use https for network targets")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = resolve_public_addresses(
        parsed.hostname,
        port,
        allow_loopback=parsed.scheme == "http" and policy.allow_local_http,
    )
    if parsed.scheme == "http" and policy.allow_local_http:
        # Local HTTP is only intended for deterministic test fixtures. Public HTTP
        # remains disabled because the anonymous scanner must be HTTPS-only.
        if not all(ipaddress.ip_address(address).is_loopback for address in addresses):
            raise UnsafeTargetError("local HTTP is only allowed for loopback fixtures")
    return value

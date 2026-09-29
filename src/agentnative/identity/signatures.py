"""HTTP message-signature verification owned by the canonical identity package."""
from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass
from typing import Any, Callable

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:  # pragma: no cover - surfaced as a fail-closed result
    InvalidSignature = Exception
    Ed25519PublicKey = None

from agentnative.identity.replay import ReplayStore


@dataclass(frozen=True)
class SignedRequest:
    method: str
    target_uri: str
    headers: dict[str, str]
    body: bytes
    signature_input: str
    signature: str


@dataclass(frozen=True)
class IntegrityResult:
    valid: bool
    reason: str
    key_id: str | None = None
    agent_id: str | None = None
    nonce: str | None = None


def content_digest(body: bytes) -> str:
    return "sha-256=" + base64.b64encode(hashlib.sha256(body).digest()).decode()


def _covered(request: SignedRequest, components: str, created: str, key_id: str, alg: str, nonce: str) -> bytes:
    lines: list[str] = []
    for component in re.findall(r'"([^"]+)"', components):
        if component == "@method":
            value = request.method.upper()
        elif component == "@target-uri":
            value = request.target_uri
        else:
            value = request.headers.get(component.lower(), request.headers.get(component, ""))
        lines.append(f'"{component}": {value}')
    lines.append(f'"@signature-params": ({components});created={created};keyid="{key_id}";alg="{alg}";nonce="{nonce}"')
    return "\n".join(lines).encode()


def verify_signed_request(
    request: SignedRequest,
    key_lookup: Callable[[str], tuple[bytes, str] | None],
    replay: ReplayStore,
    *,
    require_content_digest: bool = False,
    now: int | None = None,
) -> IntegrityResult:
    """Verify a bounded Ed25519 HTTP message signature and consume its nonce."""
    try:
        match = re.match(
            r"(?P<label>[A-Za-z][A-Za-z0-9_-]*)=\((?P<components>[^)]*)\);(?P<params>.*)$",
            request.signature_input.strip(),
        )
        if not match:
            return IntegrityResult(False, "invalid_signature")
        params = {
            item.group("key"): (item.group("quoted") if item.group("quoted") is not None else item.group("bare"))
            for item in re.finditer(
                r'(?P<key>[A-Za-z][A-Za-z0-9_-]*)=(?:"(?P<quoted>[^"]*)"|(?P<bare>[^;]+))',
                match.group("params"),
            )
        }
        key_id, alg, nonce = params.get("keyid"), params.get("alg"), params.get("nonce")
        created = int(params["created"])
        if not key_id or not nonce:
            return IntegrityResult(False, "missing_key_or_nonce")
        if alg != "ed25519":
            return IntegrityResult(False, "unsupported_algorithm", key_id, nonce=nonce)
        components = match.group("components")
        if require_content_digest and "content-digest" not in components:
            return IntegrityResult(False, "missing_signed_component", key_id, nonce=nonce)
        if "content-digest" in components and request.headers.get("content-digest") != content_digest(request.body):
            return IntegrityResult(False, "content_digest_mismatch", key_id, nonce=nonce)
        fresh, reason = replay.check_and_record(context=key_id, nonce=nonce, created=created, now=now)
        if not fresh:
            return IntegrityResult(False, reason, key_id, nonce=nonce)
        record = key_lookup(key_id)
        if record is None:
            return IntegrityResult(False, "unknown_key", key_id, nonce=nonce)
        public, agent_id = record
        encoded = request.signature.split(":", 2)[1] if request.signature.startswith(match.group("label") + "=:") else ""
        if Ed25519PublicKey is None:
            return IntegrityResult(False, "crypto_dependency_unavailable", key_id, nonce=nonce)
        Ed25519PublicKey.from_public_bytes(public).verify(
            base64.b64decode(encoded, validate=True),
            _covered(request, components, str(created), key_id, alg, nonce),
        )
        return IntegrityResult(True, "verified", key_id, agent_id, nonce)
    except (ValueError, KeyError, TypeError, base64.binascii.Error, InvalidSignature):
        return IntegrityResult(False, "invalid_signature")


__all__ = ["IntegrityResult", "SignedRequest", "_covered", "content_digest", "verify_signed_request"]

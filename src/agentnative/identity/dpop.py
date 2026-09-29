from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ec import ECDSA, SECP256R1, EllipticCurvePublicNumbers
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
    from cryptography.hazmat.primitives.hashes import SHA256
except ImportError:  # pragma: no cover - surfaced as a fail-closed result
    InvalidSignature = Exception
    ECDSA = SECP256R1 = EllipticCurvePublicNumbers = encode_dss_signature = SHA256 = None

from agentnative.identity.evidence import EvidenceStatus
from agentnative.identity.replay import ReplayStore


@dataclass(frozen=True)
class DPoPVerification:
    status: EvidenceStatus
    reason: str
    key_thumbprint: str | None = None
    proof_id: str | None = None


def _b64json(value: str) -> dict[str, object]:
    padded = value + "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode()))


def verify_dpop_proof(
    proof: str,
    *,
    method: str,
    target_uri: str,
    replay: ReplayStore,
    access_token: str | None = None,
    expected_nonce: str | None = None,
    now: int | None = None,
) -> DPoPVerification:
    """Verify a DPoP proof without acting as an OAuth authorization server."""
    try:
        parts = proof.split(".")
        if len(parts) != 3:
            return DPoPVerification(EvidenceStatus.INVALID, "malformed_proof")
        header, payload = _b64json(parts[0]), _b64json(parts[1])
        if header.get("typ") != "dpop+jwt" or header.get("alg") != "ES256":
            return DPoPVerification(EvidenceStatus.INVALID, "unsupported_or_missing_algorithm")
        jwk = header.get("jwk")
        if not isinstance(jwk, dict) or jwk.get("kty") != "EC" or jwk.get("crv") != "P-256":
            return DPoPVerification(EvidenceStatus.INVALID, "malformed_jwk")
        if not all(isinstance(jwk.get(item), str) for item in ("x", "y")):
            return DPoPVerification(EvidenceStatus.INVALID, "malformed_jwk")
        thumbprint = base64.urlsafe_b64encode(
            hashlib.sha256(
                json.dumps(
                    {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"], "y": jwk["y"]},
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode()
            ).digest()
        ).rstrip(b"=").decode()
        required = ("htm", "htu", "iat", "jti")
        if any(field not in payload for field in required):
            return DPoPVerification(EvidenceStatus.INVALID, "missing_required_claim", thumbprint)
        if payload["htm"].upper() != method.upper() or payload["htu"] != target_uri:
            return DPoPVerification(EvidenceStatus.INVALID, "method_or_uri_mismatch", thumbprint, str(payload.get("jti")))
        current = now if now is not None else int(datetime.now(timezone.utc).timestamp())
        if not isinstance(payload["iat"], int) or abs(current - payload["iat"]) > 300:
            return DPoPVerification(EvidenceStatus.INVALID, "stale_or_future_proof", thumbprint, str(payload.get("jti")))
        if expected_nonce is not None and payload.get("nonce") != expected_nonce:
            return DPoPVerification(EvidenceStatus.INVALID, "nonce_mismatch", thumbprint, str(payload.get("jti")))
        if access_token is not None:
            expected_ath = base64.urlsafe_b64encode(hashlib.sha256(access_token.encode()).digest()).rstrip(b"=").decode()
            if payload.get("ath") != expected_ath:
                return DPoPVerification(EvidenceStatus.INVALID, "access_token_hash_mismatch", thumbprint, str(payload.get("jti")))
        fresh, reason = replay.check_and_record(context="dpop:" + thumbprint, nonce=str(payload["jti"]), created=payload["iat"], now=current)
        if not fresh:
            return DPoPVerification(EvidenceStatus.INVALID, reason, thumbprint, str(payload["jti"]))
        if ECDSA is None:
            return DPoPVerification(EvidenceStatus.INVALID, "crypto_dependency_unavailable", thumbprint, str(payload["jti"]))
        x = int.from_bytes(base64.urlsafe_b64decode(jwk["x"] + "=" * (-len(jwk["x"]) % 4)), "big")
        y = int.from_bytes(base64.urlsafe_b64decode(jwk["y"] + "=" * (-len(jwk["y"]) % 4)), "big")
        public = EllipticCurvePublicNumbers(x, y, SECP256R1()).public_key()
        signature = base64.urlsafe_b64decode(parts[2] + "=" * (-len(parts[2]) % 4))
        if len(signature) != 64:
            return DPoPVerification(EvidenceStatus.INVALID, "malformed_signature", thumbprint, str(payload["jti"]))
        public.verify(
            encode_dss_signature(int.from_bytes(signature[:32], "big"), int.from_bytes(signature[32:], "big")),
            (parts[0] + "." + parts[1]).encode(),
            ECDSA(SHA256()),
        )
        return DPoPVerification(EvidenceStatus.VERIFIED, "proof_verified", thumbprint, str(payload["jti"]))
    except (ValueError, KeyError, TypeError, InvalidSignature, json.JSONDecodeError):
        return DPoPVerification(EvidenceStatus.INVALID, "proof_verification_failed")


__all__ = ["DPoPVerification", "EvidenceStatus", "verify_dpop_proof"]

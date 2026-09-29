from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from agentnative.packs.models import Pack
from agentnative.transactions.core import stable_hash


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str).encode("utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class DependencyLock:
    entries: tuple[Mapping[str, str], ...] = ()

    @property
    def lock_hash(self) -> str:
        return stable_hash([dict(item) for item in self.entries])

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": "1.0", "entries": [dict(item) for item in self.entries], "lock_hash": self.lock_hash}


@dataclass(frozen=True)
class PackTrustPolicy:
    environment: str = "SANDBOX"
    required_signatures: int = 1
    trusted_publishers: tuple[str, ...] = ()
    trusted_key_ids: tuple[str, ...] = ()
    allowed_algorithms: tuple[str, ...] = ("Ed25519",)
    allow_unsigned_seed_packs: bool = False


@dataclass(frozen=True)
class PackSignatureEnvelope:
    algorithm: str
    key_id: str
    value: str
    signed_at: str
    dependency_lock_hash: str = ""
    publisher: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"algorithm": self.algorithm, "key_id": self.key_id, "value": self.value, "signed_at": self.signed_at, "dependency_lock_hash": self.dependency_lock_hash, "publisher": self.publisher}


def pack_signed_payload(pack: Pack, *, dependency_lock_hash: str = "") -> dict[str, Any]:
    return {
        "pack_id": pack.pack_id,
        "pack_version": pack.manifest.pack_version,
        "pack_schema_version": pack.manifest.pack_schema_version,
        "content_hash": pack.content_hash,
        "core_version_requirement": pack.manifest.core_version_requirement,
        "required_core_guarantees": list(pack.manifest.required_core_guarantees),
        "dependency_lock_hash": dependency_lock_hash,
        "effective_at": pack.manifest.effective_at,
        "sunset_at": pack.manifest.sunset_at,
    }


class PackSignatureError(ValueError):
    pass


class PackSigner:
    def sign(self, pack: Pack, private_key: Any, *, key_id: str, dependency_lock: DependencyLock | None = None, publisher: str = "") -> PackSignatureEnvelope:
        lock_hash = dependency_lock.lock_hash if dependency_lock else ""
        try:
            signature = private_key.sign(_canonical(pack_signed_payload(pack, dependency_lock_hash=lock_hash)))
        except AttributeError as exc:
            raise PackSignatureError("private key does not support the approved signing interface") from exc
        return PackSignatureEnvelope("Ed25519", key_id, base64.b64encode(signature).decode("ascii"), _now(), lock_hash, publisher)


class PackSignatureVerifier:
    def verify(self, pack: Pack, envelope: PackSignatureEnvelope, *, public_keys: Mapping[str, Any], policy: PackTrustPolicy, dependency_lock: DependencyLock | None = None) -> None:
        if envelope.algorithm not in policy.allowed_algorithms:
            raise PackSignatureError("pack signature algorithm is not allowed by policy")
        if envelope.key_id not in policy.trusted_key_ids:
            raise PackSignatureError("pack signing key is not trusted for this environment")
        if policy.trusted_publishers and envelope.publisher not in policy.trusted_publishers:
            raise PackSignatureError("pack publisher is not trusted for this environment")
        expected_lock_hash = dependency_lock.lock_hash if dependency_lock else ""
        if envelope.dependency_lock_hash != expected_lock_hash:
            raise PackSignatureError("pack dependency lock hash mismatch")
        key = public_keys.get(envelope.key_id)
        if key is None:
            raise PackSignatureError("pack signing public key is unavailable")
        try:
            key.verify(base64.b64decode(envelope.value), _canonical(pack_signed_payload(pack, dependency_lock_hash=expected_lock_hash)))
        except Exception as exc:
            raise PackSignatureError("pack signature is invalid") from exc


def parse_signature(value: Any) -> PackSignatureEnvelope | None:
    if not isinstance(value, dict):
        return None
    required = {"algorithm", "key_id", "value"}
    if not required.issubset(value):
        return None
    return PackSignatureEnvelope(str(value["algorithm"]), str(value["key_id"]), str(value["value"]), str(value.get("signed_at", "")), str(value.get("dependency_lock_hash", "")), str(value.get("publisher", "")))


__all__ = ["DependencyLock", "PackSignatureEnvelope", "PackSignatureError", "PackSignatureVerifier", "PackSigner", "PackTrustPolicy", "pack_signed_payload", "parse_signature"]

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from agentnative.transactions.core import stable_hash


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str).encode("utf-8")


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class CoreGuarantee:
    guarantee_id: str
    verified: bool
    evidence_ref: str | None = None
    independently_verified: bool = False
    core_version: str = ""
    status: str = "VERIFIED"
    attestation_id: str | None = None
    fixture_only: bool = False


class CoreGuaranteeError(RuntimeError):
    pass


@dataclass(frozen=True)
class AttestationSubject:
    repository: str
    commit_sha: str
    package_version: str
    core_content_hash: str

    def to_dict(self) -> dict[str, str]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class AttestedGuarantee:
    guarantee_id: str
    status: str
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"guarantee_id": self.guarantee_id, "status": self.status, "evidence_refs": list(self.evidence_refs)}


@dataclass(frozen=True)
class CoreGuaranteeAttestation:
    attestation_id: str
    schema_version: str
    subject: AttestationSubject
    guarantees: tuple[AttestedGuarantee, ...]
    audit_run_id: str
    auditor_id: str
    issued_at: str
    expires_at: str
    toolchain_versions: Mapping[str, str] = field(default_factory=dict)
    algorithm: str = "Ed25519"
    key_id: str = ""
    signature: str = ""
    revoked_at: str | None = None

    def unsigned_payload(self) -> dict[str, Any]:
        return {
            "attestation_id": self.attestation_id,
            "schema_version": self.schema_version,
            "subject": self.subject.to_dict(),
            "guarantees": [item.to_dict() for item in self.guarantees],
            "audit": {
                "audit_run_id": self.audit_run_id,
                "auditor_id": self.auditor_id,
                "issued_at": self.issued_at,
                "expires_at": self.expires_at,
                "toolchain_versions": dict(self.toolchain_versions),
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_payload(), "signature": {"algorithm": self.algorithm, "key_id": self.key_id, "value": self.signature}, "revoked_at": self.revoked_at}

    @property
    def content_hash(self) -> str:
        return stable_hash(self.unsigned_payload())

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "CoreGuaranteeAttestation":
        subject = raw.get("subject") or {}
        audit = raw.get("audit") or {}
        signature = raw.get("signature") or {}
        return cls(
            str(raw["attestation_id"]), str(raw.get("schema_version", "1.0")),
            AttestationSubject(str(subject["repository"]), str(subject["commit_sha"]), str(subject["package_version"]), str(subject["core_content_hash"])),
            tuple(AttestedGuarantee(str(item["guarantee_id"]), str(item["status"]), tuple(str(ref) for ref in item.get("evidence_refs", []))) for item in raw.get("guarantees", [])),
            str(audit["audit_run_id"]), str(audit["auditor_id"]), str(audit["issued_at"]), str(audit["expires_at"]), dict(audit.get("toolchain_versions", {})), str(signature.get("algorithm", "")), str(signature.get("key_id", "")), str(signature.get("value", "")), raw.get("revoked_at"),
        )

    def sign(self, private_key: Any) -> "CoreGuaranteeAttestation":
        try:
            signature = private_key.sign(_canonical(self.unsigned_payload()))
        except AttributeError as exc:
            raise CoreGuaranteeError("private key does not support the approved signing interface") from exc
        return CoreGuaranteeAttestation(**{**self.__dict__, "signature": base64.b64encode(signature).decode("ascii")})


@dataclass(frozen=True)
class TrustedAttestationKey:
    key_id: str
    public_key: Any
    environment: str = "SANDBOX"
    active_from: str | None = None
    expires_at: str | None = None
    revoked_at: str | None = None
    replacement_key_id: str | None = None

    def usable(self, now: datetime | None = None) -> bool:
        moment = now or _now()
        return not self.revoked_at and (not self.active_from or moment >= (_parse_time(self.active_from) or moment)) and (not self.expires_at or moment < (_parse_time(self.expires_at) or moment))


class CoreTrustStore:
    """Small explicit trust root for independently issued core attestations."""

    def __init__(self, keys: Iterable[TrustedAttestationKey] = ()) -> None:
        self._keys = {item.key_id: item for item in keys}
        self._revoked_attestations: set[str] = set()

    def add_key(self, key: TrustedAttestationKey) -> None:
        self._keys[key.key_id] = key

    def revoke_attestation(self, attestation_id: str) -> None:
        self._revoked_attestations.add(attestation_id)

    def verify(self, attestation: CoreGuaranteeAttestation, *, expected_subject: AttestationSubject | None = None, required: Iterable[str] = (), environment: str = "SANDBOX", now: datetime | None = None) -> None:
        moment = now or _now()
        if attestation.schema_version != "1.0":
            raise CoreGuaranteeError("unsupported core guarantee attestation schema")
        if expected_subject and attestation.subject != expected_subject:
            raise CoreGuaranteeError("core guarantee attestation subject does not match the running build")
        if attestation.attestation_id in self._revoked_attestations or attestation.revoked_at:
            raise CoreGuaranteeError("core guarantee attestation is revoked")
        if (_parse_time(attestation.expires_at) or moment) <= moment:
            raise CoreGuaranteeError("core guarantee attestation is expired")
        key = self._keys.get(attestation.key_id)
        if not key or key.environment != environment or not key.usable(moment):
            raise CoreGuaranteeError("attestation signing key is not trusted for this environment")
        if attestation.algorithm != "Ed25519" or not attestation.signature:
            raise CoreGuaranteeError("attestation must use a signed Ed25519 envelope")
        try:
            key.public_key.verify(base64.b64decode(attestation.signature), _canonical(attestation.unsigned_payload()))
        except Exception as exc:
            raise CoreGuaranteeError("core guarantee attestation signature is invalid") from exc
        by_id = {item.guarantee_id: item for item in attestation.guarantees}
        missing = [item for item in required if not by_id.get(item) or by_id[item].status != "VERIFIED" or not by_id[item].evidence_refs]
        if missing:
            raise CoreGuaranteeError("attestation is missing verified evidence: " + ", ".join(sorted(missing)))


class CoreGuaranteeRegistry:
    """Explicit gate for pack claims that depend on v2 safety guarantees."""

    def __init__(self, guarantees: Iterable[CoreGuarantee] = (), *, attestation: CoreGuaranteeAttestation | None = None) -> None:
        self._items = {item.guarantee_id: item for item in guarantees}
        self.attestation = attestation

    def missing(self, required: Iterable[str]) -> tuple[str, ...]:
        return tuple(sorted(guarantee_id for guarantee_id in set(required) if not (self._items.get(guarantee_id) and self._items[guarantee_id].verified and self._items[guarantee_id].independently_verified and self._items[guarantee_id].status == "VERIFIED")))

    def require(self, required: Iterable[str]) -> None:
        missing = self.missing(required)
        if missing:
            raise CoreGuaranteeError("required core guarantees are not independently verified: " + ", ".join(missing))

    def evidence(self, guarantee_id: str) -> CoreGuarantee | None:
        return self._items.get(guarantee_id)

    @property
    def is_test_fixture(self) -> bool:
        return bool(self._items) and all(item.fixture_only for item in self._items.values())

    @classmethod
    def from_attestation(cls, attestation: CoreGuaranteeAttestation, trust_store: CoreTrustStore, *, expected_subject: AttestationSubject, required: Iterable[str], environment: str = "SANDBOX") -> "CoreGuaranteeRegistry":
        trust_store.verify(attestation, expected_subject=expected_subject, required=required, environment=environment)
        items = [CoreGuarantee(item.guarantee_id, item.status == "VERIFIED", item.evidence_refs[0] if item.evidence_refs else None, item.status == "VERIFIED", attestation.subject.package_version, item.status, attestation.attestation_id) for item in attestation.guarantees]
        return cls(items, attestation=attestation)

    @classmethod
    def for_test(cls, *, core_version: str = "test") -> "CoreGuaranteeRegistry":
        """Create an explicitly fixture-only registry for unit tests and synthetic demos."""
        required = ("identity_binding_v1", "delegation_scope_v1", "transaction_identity_v1", "replay_safe_confirmation_v1", "idempotency_atomicity_v1", "receipt_integrity_v1")
        return cls(CoreGuarantee(item, True, f"test:{item}", True, core_version, "VERIFIED", "test-fixture", True) for item in required)


__all__ = ["AttestationSubject", "AttestedGuarantee", "CoreGuarantee", "CoreGuaranteeAttestation", "CoreGuaranteeError", "CoreGuaranteeRegistry", "CoreTrustStore", "TrustedAttestationKey"]

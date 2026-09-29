from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from agentnative.transactions.core import stable_hash


class DriftResult(StrEnum):
    UNCHANGED = "UNCHANGED"
    SOURCE_CHANGED = "SOURCE_CHANGED"
    VERSION_CHANGED = "VERSION_CHANGED"
    BREAKING = "BREAKING"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class ProtocolProfile:
    profile_id: str
    protocol_name: str
    protocol_version: str
    profile_version: str
    as_of: str
    source_url: str
    source_hash: str
    supported_features: tuple[str, ...] = ()
    unsupported_features: tuple[str, ...] = ()
    required_extensions: tuple[str, ...] = ()
    compatibility_status: str = "UNVERIFIED"
    last_drift_check: str = ""
    drift_result: DriftResult = DriftResult.UNCHANGED

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ProtocolProfile":
        required = {"profile_id", "protocol_name", "protocol_version", "profile_version", "as_of", "source_url", "source_hash"} - set(raw)
        if required:
            raise ValueError("protocol profile missing fields: " + ", ".join(sorted(required)))
        return cls(
            profile_id=str(raw["profile_id"]),
            protocol_name=str(raw["protocol_name"]),
            protocol_version=str(raw["protocol_version"]),
            profile_version=str(raw["profile_version"]),
            as_of=str(raw["as_of"]),
            source_url=str(raw["source_url"]),
            source_hash=str(raw["source_hash"]),
            supported_features=tuple(str(item) for item in raw.get("supported_features", [])),
            unsupported_features=tuple(str(item) for item in raw.get("unsupported_features", [])),
            required_extensions=tuple(str(item) for item in raw.get("required_extensions", [])),
            compatibility_status=str(raw.get("compatibility_status", "UNVERIFIED")),
            last_drift_check=str(raw.get("last_drift_check", "")),
            drift_result=DriftResult(str(raw.get("drift_result", DriftResult.UNCHANGED.value))),
        )

    @property
    def identity_hash(self) -> str:
        return stable_hash({
            "profile_id": self.profile_id,
            "protocol_name": self.protocol_name,
            "protocol_version": self.protocol_version,
            "profile_version": self.profile_version,
            "as_of": self.as_of,
            "source_url": self.source_url,
            "source_hash": self.source_hash,
            "supported_features": self.supported_features,
            "unsupported_features": self.unsupported_features,
            "required_extensions": self.required_extensions,
        })


@dataclass(frozen=True)
class ProtocolDriftReport:
    profile_id: str
    result: DriftResult
    changed_fields: tuple[str, ...] = ()
    breaking_changes: tuple[str, ...] = ()
    affected_capabilities: tuple[str, ...] = ()
    affected_scenarios: tuple[str, ...] = ()

    @property
    def safe_for_conformance(self) -> bool:
        return self.result == DriftResult.UNCHANGED and not self.breaking_changes


class ProtocolRegistry:
    def __init__(self) -> None:
        self._profiles: dict[str, ProtocolProfile] = {}

    def register(self, profile: ProtocolProfile) -> None:
        if profile.profile_id in self._profiles:
            raise ValueError(f"protocol profile already registered: {profile.profile_id}")
        self._profiles[profile.profile_id] = profile

    def get(self, profile_id: str) -> ProtocolProfile:
        return self._profiles[profile_id]

    def compare(self, profile_id: str, candidate: ProtocolProfile, *, affected_capabilities: tuple[str, ...] = (), affected_scenarios: tuple[str, ...] = ()) -> ProtocolDriftReport:
        current = self.get(profile_id)
        changed = []
        breaking = []
        for field_name in ("protocol_version", "profile_version", "source_hash", "supported_features", "unsupported_features", "required_extensions"):
            if getattr(current, field_name) != getattr(candidate, field_name):
                changed.append(field_name)
        if current.protocol_version != candidate.protocol_version:
            result = DriftResult.VERSION_CHANGED
        elif current.source_hash != candidate.source_hash:
            result = DriftResult.SOURCE_CHANGED
        else:
            result = DriftResult.UNCHANGED
        removed_features = set(current.supported_features) - set(candidate.supported_features)
        removed_extensions = set(current.required_extensions) - set(candidate.required_extensions)
        if removed_features:
            breaking.extend(f"removed_supported_feature:{item}" for item in sorted(removed_features))
        if removed_extensions:
            breaking.extend(f"removed_required_extension:{item}" for item in sorted(removed_extensions))
        if "authentication" in candidate.unsupported_features and "authentication" in current.supported_features:
            breaking.append("authentication_support_removed")
        if breaking:
            result = DriftResult.BREAKING
        return ProtocolDriftReport(profile_id, result, tuple(changed), tuple(breaking), affected_capabilities, affected_scenarios)


__all__ = ["DriftResult", "ProtocolDriftReport", "ProtocolProfile", "ProtocolRegistry"]

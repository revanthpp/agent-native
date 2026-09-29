from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Iterable

from agentnative.transactions.core import stable_hash


class TraceabilityError(ValueError):
    pass


class EvidenceState(StrEnum):
    KNOWN_TRUE = "KNOWN_TRUE"
    KNOWN_FALSE = "KNOWN_FALSE"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFLICTING = "CONFLICTING"
    STALE = "STALE"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class EvidenceObservation:
    field_name: str
    value: Any
    value_type: str
    source_type: str
    source_ref: str
    observed_at: datetime
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    confidence: float = 1.0
    environment: str = ""
    collector: str = ""
    tenant_id: str = ""
    pack_id: str = ""
    evidence_hash: str = ""
    state: EvidenceState = EvidenceState.UNVERIFIED

    def __post_init__(self) -> None:
        if not self.field_name.strip() or not self.source_ref.strip():
            raise ValueError("evidence field_name and source_ref are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("evidence confidence must be between 0 and 1")
        observed = self.observed_at.astimezone(timezone.utc)
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("evidence validity interval is reversed")
        computed = stable_hash({
            "field_name": self.field_name,
            "value": self.value,
            "value_type": self.value_type,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "observed_at": observed.isoformat(),
            "valid_from": self.valid_from.astimezone(timezone.utc).isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.astimezone(timezone.utc).isoformat() if self.valid_until else None,
            "environment": self.environment,
            "tenant_id": self.tenant_id,
            "pack_id": self.pack_id,
            "state": self.state.value,
        })
        if self.evidence_hash and self.evidence_hash != computed:
            raise ValueError("evidence hash mismatch")
        object.__setattr__(self, "evidence_hash", computed)

    def current_state(self, *, now: datetime | None = None, stale_after_seconds: int | None = None) -> EvidenceState:
        if self.state in {EvidenceState.CONFLICTING, EvidenceState.NOT_APPLICABLE, EvidenceState.UNVERIFIED}:
            return self.state
        clock = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if self.valid_until and clock > self.valid_until:
            return EvidenceState.STALE
        if stale_after_seconds is not None and (clock - self.observed_at.astimezone(timezone.utc)).total_seconds() > stale_after_seconds:
            return EvidenceState.STALE
        return self.state


class EvidenceStore:
    """Tenant/pack-scoped evidence store with explicit conflict semantics."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str, str], list[EvidenceObservation]] = {}

    def add(self, observation: EvidenceObservation) -> EvidenceObservation:
        key = (observation.tenant_id, observation.pack_id, observation.field_name)
        current = self._items.setdefault(key, [])
        if current and any(item.value != observation.value and item.state not in {EvidenceState.NOT_APPLICABLE, EvidenceState.UNVERIFIED} for item in current):
            observation = EvidenceObservation(
                **{**observation.__dict__, "state": EvidenceState.CONFLICTING, "evidence_hash": ""}
            )
            current[:] = [
                EvidenceObservation(**{**item.__dict__, "state": EvidenceState.CONFLICTING, "evidence_hash": ""})
                for item in current
            ]
        current.append(observation)
        return observation

    def get(self, *, tenant_id: str, pack_id: str, field_name: str, now: datetime | None = None) -> tuple[EvidenceObservation, ...]:
        return tuple(item for item in self._items.get((tenant_id, pack_id, field_name), ()) if item.current_state(now=now) != EvidenceState.STALE)

    def state(self, *, tenant_id: str, pack_id: str, field_name: str, now: datetime | None = None, stale_after_seconds: int | None = None) -> EvidenceState:
        items = self._items.get((tenant_id, pack_id, field_name), ())
        if not items:
            return EvidenceState.UNKNOWN
        states = {item.current_state(now=now, stale_after_seconds=stale_after_seconds) for item in items}
        if EvidenceState.CONFLICTING in states:
            return EvidenceState.CONFLICTING
        if EvidenceState.STALE in states:
            return EvidenceState.STALE
        return next(iter(states))


@dataclass(frozen=True)
class TraceabilityRecord:
    requirement_id: str
    control_id: str
    evidence_id: str
    evaluation_id: str
    recommendation_id: str


def validate_traceability(records: Iterable[TraceabilityRecord]) -> None:
    records = tuple(records)
    if not records:
        raise TraceabilityError("at least one traceability record is required")
    for index, record in enumerate(records):
        for field_name in ("requirement_id", "control_id", "evidence_id", "evaluation_id", "recommendation_id"):
            if not getattr(record, field_name).strip():
                raise TraceabilityError(f"record {index} has empty {field_name}")


__all__ = ["TraceabilityError", "TraceabilityRecord", "validate_traceability"]

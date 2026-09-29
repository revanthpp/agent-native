from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class TraceabilityError(ValueError):
    pass


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

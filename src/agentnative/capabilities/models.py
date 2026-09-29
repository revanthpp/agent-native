from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agentnative.protocols.models import ActionClass, EvidenceRef, SideEffect


@dataclass
class Capability:
    capability_id: str
    business_id: str
    name: str
    description: str = ""
    protocol_sources: list[str] = field(default_factory=list)
    action_class: ActionClass = ActionClass.UNKNOWN
    resource_types: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    auth_requirements: list[dict[str, Any]] = field(default_factory=list)
    required_scopes: list[str] = field(default_factory=list)
    side_effect: SideEffect = SideEffect.UNKNOWN
    reversibility: str = "unknown"
    confirmation: str = "unknown"
    idempotency: str = "unknown"
    value_boundary: dict[str, Any] = field(default_factory=dict)
    data_sensitivity: str = "unknown"
    human_escalation: bool = False
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


__all__ = ["ActionClass", "Capability", "EvidenceRef", "SideEffect"]

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from agentnative.capabilities.models import Capability
from agentnative.protocols.models import ActionClass, EvidenceRef, SideEffect


class EvalScenarioCategory(StrEnum):
    POSITIVE = "positive"
    PARTIAL_MATURITY = "partial-maturity"
    DECEPTIVE = "deceptive"
    MALFORMED = "malformed"
    HIGH_RISK = "high-risk"


@dataclass(frozen=True)
class CapabilityProfile:
    """Sector semantics that compile into the canonical v2 Capability."""

    capability_id: str
    name: str
    group: str
    action_class: ActionClass = ActionClass.UNKNOWN
    side_effect: SideEffect = SideEffect.UNKNOWN
    resource_types: tuple[str, ...] = ()
    required_scopes: tuple[str, ...] = ()
    reversibility: str = "unknown"
    confirmation: str = "unknown"
    idempotency: str = "unknown"
    data_sensitivity: str = "unknown"
    human_escalation: bool = False
    description: str = ""

    def to_capability(self, pack_id: str, business_id: str) -> Capability:
        return Capability(
            capability_id=f"{pack_id}:{self.capability_id}",
            business_id=business_id,
            name=f"{pack_id}.{self.capability_id}",
            description=self.description,
            protocol_sources=[f"pack:{pack_id}"],
            action_class=self.action_class,
            resource_types=list(self.resource_types),
            required_scopes=list(self.required_scopes),
            side_effect=self.side_effect,
            reversibility=self.reversibility,
            confirmation=self.confirmation,
            idempotency=self.idempotency,
            data_sensitivity=self.data_sensitivity,
            human_escalation=self.human_escalation,
            evidence_refs=[EvidenceRef(source=f"pack:{pack_id}", pointer=f"/capabilities/{self.capability_id}")],
        )


@dataclass(frozen=True)
class EvalScenario:
    scenario_id: str
    requirement_id: str
    category: EvalScenarioCategory
    title: str
    expected_outcome: str
    capability_id: str | None = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class PackManifest:
    pack_id: str
    pack_version: str
    sector: str
    subsectors: tuple[str, ...]
    core_version_requirement: str
    release_status: str
    protocol_profiles: tuple[dict[str, Any], ...] = ()
    platform_profiles: tuple[dict[str, Any], ...] = ()
    known_limitations: tuple[str, ...] = ()
    external_reference_mappings: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class Pack:
    manifest: PackManifest
    capabilities: tuple[CapabilityProfile, ...]
    risk_model: Mapping[str, Any]
    maturity_model: Mapping[str, Any]
    control_profiles: Mapping[str, Any]
    activation_strategies: tuple[str, ...]
    human_handoff_rules: tuple[str, ...]
    evaluation_scenarios: tuple[EvalScenario, ...]
    evidence_requirements: Mapping[str, Any]
    report_sections: tuple[str, ...]
    dependencies: Mapping[str, Any]

    @property
    def pack_id(self) -> str:
        return self.manifest.pack_id

    def compile_capabilities(self, business_id: str) -> list[Capability]:
        return [item.to_capability(self.pack_id, business_id) for item in self.capabilities]

    def scenario_categories(self) -> set[EvalScenarioCategory]:
        return {scenario.category for scenario in self.evaluation_scenarios}


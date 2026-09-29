from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from agentnative.packs.evidence import EvidenceObservation, EvidenceState
from agentnative.transactions.core import stable_hash


class ActivationPattern(StrEnum):
    DIRECT = "DIRECT"
    PLATFORM_MEDIATED = "PLATFORM_MEDIATED"
    AGGREGATOR_MARKETPLACE = "AGGREGATOR_MARKETPLACE"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"
    DO_NOT_ACTIVATE = "DO_NOT_ACTIVATE"


@dataclass(frozen=True)
class ActivationInputs:
    business_size: str
    technical_capacity: str
    api_maturity: str
    existing_platforms: tuple[str, ...] = ()
    transaction_volume: str = "unknown"
    action_value: str = "unknown"
    data_sensitivity: str = "unknown"
    regulatory_sensitivity: str = "unknown"
    reversibility: str = "unknown"
    customer_identity_requirement: str = "unknown"
    payment_requirement: str = "none"
    real_time_inventory_requirement: bool = False
    human_staff_availability: str = "unknown"
    agent_channel_priority: str = "unknown"
    expected_agent_volume: int = 0
    protocol_platform_fee_per_action: float | None = None
    connector_cost_per_action: float | None = None
    inference_cost_per_action: float | None = None
    human_handoff_cost_per_action: float | None = None
    margin_per_action: float | None = None
    cost_ceiling_per_action: float | None = None
    observations: tuple[EvidenceObservation, ...] = ()
    tenant_id: str = ""
    pack_id: str = ""
    environment: str = ""

    def __post_init__(self) -> None:
        vocabularies = {
            "business_size": {"unknown", "micro", "small", "medium", "large", "enterprise"},
            "technical_capacity": {"unknown", "none", "low", "medium", "high"},
            "api_maturity": {"unknown", "none", "early", "moderate", "mature", "advanced"},
            "data_sensitivity": {"unknown", "low", "medium", "high", "regulated"},
            "regulatory_sensitivity": {"unknown", "low", "medium", "high", "regulated"},
            "human_staff_availability": {"unknown", "none", "low", "medium", "high"},
        }
        for field_name, allowed in vocabularies.items():
            value = str(getattr(self, field_name)).strip().lower()
            if value not in allowed:
                raise ValueError(f"{field_name} must be one of {sorted(allowed)}")
        if self.expected_agent_volume < 0:
            raise ValueError("expected_agent_volume cannot be negative")


@dataclass(frozen=True)
class ActivationRecommendation:
    recommended_pattern: ActivationPattern
    viable_alternatives: tuple[ActivationPattern, ...]
    rationale: tuple[str, ...]
    prerequisites: tuple[str, ...]
    integration_complexity: str
    security_implications: tuple[str, ...]
    operating_model_implications: tuple[str, ...]
    first_implementation_milestone: str
    assumptions: tuple[str, ...]
    overridden: bool = False
    override_reason: str | None = None
    recommendation_id: str = ""
    rejected_patterns: tuple[ActivationPattern, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    economic_implications: tuple[str, ...] = ()
    residual_risks: tuple[str, ...] = ()
    pack_id: str = ""
    pack_version: str = ""
    pack_hash: str = ""
    engine_version: str = "3a.1"
    generated_at: str = ""
    override_owner: str | None = None
    override_timestamp: str | None = None
    reason_codes: tuple[str, ...] = ()
    satisfied_prerequisites: tuple[str, ...] = ()
    blocking_prerequisites: tuple[str, ...] = ()
    applied_policy_rules: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended_pattern": self.recommended_pattern.value,
            "viable_alternatives": [item.value for item in self.viable_alternatives],
            "rationale": list(self.rationale),
            "prerequisites": list(self.prerequisites),
            "integration_complexity": self.integration_complexity,
            "security_implications": list(self.security_implications),
            "operating_model_implications": list(self.operating_model_implications),
            "first_implementation_milestone": self.first_implementation_milestone,
            "assumptions": list(self.assumptions),
            "overridden": self.overridden,
            "override_reason": self.override_reason,
            "recommendation_id": self.recommendation_id,
            "rejected_patterns": [item.value for item in self.rejected_patterns],
            "evidence_refs": list(self.evidence_refs),
            "unknowns": list(self.unknowns),
            "conflicts": list(self.conflicts),
            "economic_implications": list(self.economic_implications),
            "residual_risks": list(self.residual_risks),
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "pack_hash": self.pack_hash,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "override_owner": self.override_owner,
            "override_timestamp": self.override_timestamp,
            "reason_codes": list(self.reason_codes),
            "satisfied_prerequisites": list(self.satisfied_prerequisites),
            "blocking_prerequisites": list(self.blocking_prerequisites),
            "applied_policy_rules": list(self.applied_policy_rules),
        }


def _rank(value: str, values: tuple[str, ...]) -> int:
    normalized = value.strip().lower()
    try:
        return values.index(normalized)
    except ValueError:
        return 0


class ActivationStrategyEngine:
    """Small, explainable recommendation engine; never emits an opaque score."""

    _capacity = ("none", "low", "medium", "high")
    _maturity = ("unknown", "none", "early", "moderate", "mature", "advanced")
    _sensitivity = ("low", "medium", "high", "regulated")

    def recommend(self, inputs: ActivationInputs, *, override: ActivationPattern | None = None, override_reason: str | None = None, decision_owner: str | None = None, pack_version: str = "", pack_hash: str = "", engine_version: str = "3a.1") -> ActivationRecommendation:
        has_platform = bool(inputs.existing_platforms)
        low_capacity = _rank(inputs.technical_capacity, self._capacity) <= 1
        mature_api = _rank(inputs.api_maturity, self._maturity) >= 4
        high_consequence = (
            _rank(inputs.data_sensitivity, self._sensitivity) >= 2
            or _rank(inputs.regulatory_sensitivity, self._sensitivity) >= 2
            or inputs.reversibility.strip().lower() in {"irreversible", "low"}
            or inputs.action_value.strip().lower() in {"high", "very_high", "very-high"}
        )
        staff_available = _rank(inputs.human_staff_availability, self._capacity) >= 2

        economic_viability, economic_implications = self._economics(inputs)
        if economic_viability == "NOT_VIABLE":
            recommended = ActivationPattern.DO_NOT_ACTIVATE
            rationale = ("The modeled per-action cost exceeds the available margin or configured ceiling.", "Run a limited evidence-gathering pilot only if the economics are revisited with observed data.")
        elif high_consequence and not mature_api and not has_platform and not staff_available:
            recommended = ActivationPattern.DO_NOT_ACTIVATE
            rationale = ("The workflow has high consequence or sensitivity but no mature interface, platform control, or human operating capacity.", "There is no defensible activation boundary in the supplied evidence.")
        elif high_consequence and not mature_api:
            recommended = ActivationPattern.HUMAN_HANDOFF
            rationale = ("The workflow has high consequence or sensitivity but lacks mature machine-facing controls.", "Human review is the safest first activation boundary while capability and recovery evidence are built.")
        elif low_capacity and has_platform:
            recommended = ActivationPattern.PLATFORM_MEDIATED
            rationale = ("Existing platform leverage is available and internal technical capacity is limited.", "A mediated path can activate the journey without forcing the business to become an API operator.")
        elif mature_api and _rank(inputs.technical_capacity, self._capacity) >= 2:
            recommended = ActivationPattern.DIRECT
            rationale = ("The business has mature interfaces and enough technical capacity to own the agent boundary.", "Direct participation maximizes control when the expected volume or strategic value justifies operating it.")
        elif has_platform:
            recommended = ActivationPattern.PLATFORM_MEDIATED
            rationale = ("A relevant platform already owns part of the workflow.", "The platform should be evaluated as the shortest activation path before custom infrastructure is recommended.")
        elif staff_available:
            recommended = ActivationPattern.HUMAN_HANDOFF
            rationale = ("The business can support a person in the loop while its machine-facing surface matures.", "Human handoff preserves useful discovery and lead capture without pretending unsupported actions are safe.")
        else:
            recommended = ActivationPattern.AGGREGATOR_MARKETPLACE
            rationale = ("No mature direct interface or platform path is established.", "An intermediary may provide distribution while the business validates demand and control requirements.")

        alternatives = self._alternatives(recommended, inputs, high_consequence, has_platform, mature_api, staff_available)
        complexity = self._complexity(recommended, inputs, high_consequence)
        recommendation = ActivationRecommendation(
            recommended_pattern=override or recommended,
            viable_alternatives=tuple(item for item in alternatives if item != (override or recommended)),
            rationale=rationale if override is None else rationale + (f"The client selected {override.value} instead of the engine recommendation.",),
            prerequisites=self._prerequisites(recommended, inputs, high_consequence),
            integration_complexity=complexity,
            security_implications=self._security_implications(recommended, inputs),
            operating_model_implications=self._operating_implications(recommended),
            first_implementation_milestone=self._milestone(recommended, inputs),
            assumptions=self._assumptions(inputs, has_platform, mature_api),
            overridden=override is not None and override != recommended,
            override_reason=override_reason if override is not None and override != recommended else None,
            recommendation_id=stable_hash(self._canonical_inputs(inputs, pack_version, pack_hash, engine_version))[:24],
            rejected_patterns=tuple(item for item in ActivationPattern if item not in {override or recommended, *alternatives}),
            evidence_refs=tuple(item.evidence_hash for item in inputs.observations),
            unknowns=tuple(sorted({item.field_name for item in inputs.observations if item.current_state() in {EvidenceState.UNKNOWN, EvidenceState.UNVERIFIED, EvidenceState.STALE}})),
            conflicts=tuple(sorted({item.field_name for item in inputs.observations if item.current_state() == EvidenceState.CONFLICTING})),
            economic_implications=economic_implications,
            residual_risks=self._residual_risks(inputs, recommended),
            pack_id=inputs.pack_id,
            pack_version=pack_version,
            pack_hash=pack_hash,
            engine_version=engine_version,
            generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            override_owner=decision_owner if override is not None and override != recommended else None,
            override_timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z") if override is not None and override != recommended else None,
        )
        if recommendation.overridden and (not override_reason or not decision_owner):
            raise ValueError("an activation override requires an owner and rationale")
        return recommendation

    def _alternatives(self, recommended: ActivationPattern, inputs: ActivationInputs, high_consequence: bool, has_platform: bool, mature_api: bool, staff_available: bool) -> list[ActivationPattern]:
        if recommended == ActivationPattern.DO_NOT_ACTIVATE:
            return [ActivationPattern.DO_NOT_ACTIVATE]
        candidates = []
        if has_platform:
            candidates.append(ActivationPattern.PLATFORM_MEDIATED)
        if mature_api:
            candidates.append(ActivationPattern.DIRECT)
        if staff_available or high_consequence:
            candidates.append(ActivationPattern.HUMAN_HANDOFF)
        if inputs.agent_channel_priority in {"discovery", "distribution", "marketplace"}:
            candidates.append(ActivationPattern.AGGREGATOR_MARKETPLACE)
        return list(dict.fromkeys([recommended, *candidates]))

    def _economics(self, inputs: ActivationInputs) -> tuple[str, tuple[str, ...]]:
        values = (
            inputs.protocol_platform_fee_per_action,
            inputs.connector_cost_per_action,
            inputs.inference_cost_per_action,
            inputs.human_handoff_cost_per_action,
        )
        if any(value is None for value in values) or inputs.margin_per_action is None:
            return "UNKNOWN", ("Economic evidence is incomplete; cost, margin, and exception assumptions require observation.",)
        estimated = sum(value or 0 for value in values)
        implications = (f"Estimated variable cost per action is {estimated:.4f}.", f"Modeled margin per action is {inputs.margin_per_action:.4f}.")
        if estimated > inputs.margin_per_action or (inputs.cost_ceiling_per_action is not None and estimated > inputs.cost_ceiling_per_action):
            return "NOT_VIABLE", implications + ("The modeled unit economics fail the configured viability boundary.",)
        return "VIABLE", implications + ("The modeled unit economics clear the configured viability boundary; validate with observed pilot data.",)

    def _canonical_inputs(self, inputs: ActivationInputs, pack_version: str, pack_hash: str, engine_version: str) -> dict[str, Any]:
        return {
            "inputs": {key: value for key, value in inputs.__dict__.items() if key != "observations"},
            "observations": sorted(item.evidence_hash for item in inputs.observations),
            "pack_version": pack_version,
            "pack_hash": pack_hash,
            "engine_version": engine_version,
        }

    def _residual_risks(self, inputs: ActivationInputs, pattern: ActivationPattern) -> tuple[str, ...]:
        risks = []
        if inputs.api_maturity in {"unknown", "none", "early"}:
            risks.append("Machine-facing capability behavior is not independently verified.")
        if inputs.data_sensitivity in {"unknown", "high", "regulated"}:
            risks.append("Data-access boundaries require explicit minimum-necessary validation.")
        if pattern == ActivationPattern.DO_NOT_ACTIVATE:
            risks.append("No activation path is recommended until missing controls, evidence, or economics change.")
        return tuple(risks)

    def _complexity(self, pattern: ActivationPattern, inputs: ActivationInputs, high_consequence: bool) -> str:
        if pattern == ActivationPattern.HUMAN_HANDOFF:
            return "LOW" if not high_consequence else "MEDIUM"
        if pattern == ActivationPattern.PLATFORM_MEDIATED:
            return "MEDIUM" if inputs.existing_platforms else "HIGH"
        if pattern == ActivationPattern.AGGREGATOR_MARKETPLACE:
            return "MEDIUM"
        return "HIGH" if high_consequence or inputs.real_time_inventory_requirement else "MEDIUM"

    def _prerequisites(self, pattern: ActivationPattern, inputs: ActivationInputs, high_consequence: bool) -> tuple[str, ...]:
        common = ["Define the first bounded journey and its deny conditions.", "Run the journey through synthetic simulation before production exposure."]
        if pattern == ActivationPattern.PLATFORM_MEDIATED:
            common += [f"Verify connector support and controls for: {', '.join(inputs.existing_platforms)}.", "Confirm the platform exposes enough evidence for retries, handoff, and recovery."]
        elif pattern == ActivationPattern.DIRECT:
            common += ["Publish stable capability identifiers and explicit authorization semantics.", "Provide idempotency, recovery, and receipt correlation for state-changing actions."]
        elif pattern == ActivationPattern.AGGREGATOR_MARKETPLACE:
            common += ["Document intermediary identity, delegation, and failure boundaries.", "Define a fallback when the intermediary is unavailable."]
        else:
            common += ["Define owner/operator handoff channels and service-level expectations.", "Represent unsupported actions as machine-readable human handoff, not implicit success."]
        if high_consequence:
            common.append("Require explicit confirmation or stronger authority for consequential actions.")
        return tuple(common)

    def _security_implications(self, pattern: ActivationPattern, inputs: ActivationInputs) -> tuple[str, ...]:
        implications = ["Keep agent identity, principal authority, and business policy as separate decisions."]
        if pattern == ActivationPattern.PLATFORM_MEDIATED:
            implications.append("Treat the platform as an intermediary with its own privilege and outage boundary.")
        elif pattern == ActivationPattern.AGGREGATOR_MARKETPLACE:
            implications.append("Prevent identity laundering and overbroad delegation through the intermediary.")
        elif pattern == ActivationPattern.DIRECT:
            implications.append("The business owns its public agent boundary, revocation, rate limits, and recovery behavior.")
        else:
            implications.append("Minimize data shared before human review and log the handoff outcome.")
        if inputs.data_sensitivity.strip().lower() in {"high", "regulated"}:
            implications.append("Apply minimum-necessary data access and redacted evidence by default.")
        return tuple(implications)

    def _operating_implications(self, pattern: ActivationPattern) -> tuple[str, ...]:
        if pattern == ActivationPattern.DO_NOT_ACTIVATE:
            return ("Do not expose the requested journey to external agents.", "Use the residual-risk record to define the next evidence or control milestone.")
        return {
            ActivationPattern.DIRECT: ("Own ongoing protocol, policy, and incident operations.", "Provide an owner for activation changes and emergency disablement."),
            ActivationPattern.PLATFORM_MEDIATED: ("Manage platform configuration and connector credentials.", "Track platform limits, version changes, and outage fallback."),
            ActivationPattern.AGGREGATOR_MARKETPLACE: ("Manage listing quality, intermediary terms, and escalation paths.", "Accept less direct control in exchange for distribution."),
            ActivationPattern.HUMAN_HANDOFF: ("Train staff on agent-originated requests and escalation boundaries.", "Measure handoff volume and response time before increasing autonomy."),
        }[pattern]

    def _milestone(self, pattern: ActivationPattern, inputs: ActivationInputs) -> str:
        if pattern == ActivationPattern.HUMAN_HANDOFF:
            return "Launch one discover → collect context → human handoff journey with explicit owner controls."
        if pattern == ActivationPattern.PLATFORM_MEDIATED:
            return "Connect one existing platform in a sandbox and prove one bounded journey with evidence."
        if pattern == ActivationPattern.AGGREGATOR_MARKETPLACE:
            return "Publish one low-risk capability through the intermediary and validate identity, handoff, and recovery."
        return "Expose one bounded, low-risk direct capability with policy, idempotency, trace, and receipt evidence."

    def _assumptions(self, inputs: ActivationInputs, has_platform: bool, mature_api: bool) -> tuple[str, ...]:
        return (
            f"Existing platforms were reported as: {', '.join(inputs.existing_platforms) if has_platform else 'none'}.",
            f"API maturity was self-described as {inputs.api_maturity}; the engine does not independently verify it.",
            "The recommendation is a starting hypothesis and must be validated against executable evidence.",
        )


__all__ = ["ActivationInputs", "ActivationPattern", "ActivationRecommendation", "ActivationStrategyEngine"]

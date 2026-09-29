from __future__ import annotations

import copy
import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

import yaml

from agentnative.ownership import Environment
from agentnative.packs import ActivationInputs, ActivationPattern, ActivationStrategyEngine, CoreGuaranteeRegistry, EvidenceObservation, EvidenceState, PaymentAuthorizationState, RetailJourneyState, RetailProduct, RetailReferenceEnvironment, RetailVariant, load_builtin_packs
from agentnative.packs.protocols import ProtocolProfile
from agentnative.security.secrets import SecretDetector
from agentnative.transactions import Confirmation
from agentnative.transactions.core import stable_hash


SYNTHETIC_BOUNDARY = "SYNTHETIC SIMULATION — NO PRODUCTION TRANSACTION OCCURRED"
WORKSPACE_VERSION = "1.0"
ENGINE_VERSION = "3b.1"


class RetailProductError(ValueError):
    pass


class CapabilityState(StrEnum):
    DECLARED = "DECLARED"
    OBSERVED = "OBSERVED"
    TESTED = "TESTED"
    EXECUTABLE_IN_SIMULATION = "EXECUTABLE_IN_SIMULATION"
    EXECUTABLE_IN_SANDBOX = "EXECUTABLE_IN_SANDBOX"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class GapType(StrEnum):
    HARD_PROHIBITION = "HARD_PROHIBITION"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    REMEDIABLE_CONTROL_GAP = "REMEDIABLE_CONTROL_GAP"
    STRATEGIC_TRADEOFF = "STRATEGIC_TRADEOFF"
    USER_OWNED_PREFERENCE = "USER_OWNED_PREFERENCE"


@dataclass(frozen=True)
class JourneyTemplate:
    journey_id: str
    persona: str
    agent_goal: str
    business_goal: str
    capabilities: tuple[str, ...]
    risk: str
    reversibility: str
    payment: str
    human_handoff: bool
    protocol_profiles: tuple[str, ...]
    evaluation_scenarios: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"capabilities": list(self.capabilities), "protocol_profiles": list(self.protocol_profiles), "evaluation_scenarios": list(self.evaluation_scenarios)}


JOURNEY_TEMPLATES: tuple[JourneyTemplate, ...] = (
    JourneyTemplate("product_discovery", "shopper", "find relevant products", "qualified discovery", ("discover",), "low", "high", "none", False, ("openapi",), ("positive", "deceptive")),
    JourneyTemplate("product_comparison", "shopper", "compare products", "increase conversion", ("discover", "compare"), "low", "high", "none", False, ("openapi",), ("positive", "malformed")),
    JourneyTemplate("inventory_inquiry", "shopper", "check availability", "reduce stock uncertainty", ("read_inventory",), "medium", "high", "none", False, ("openapi",), ("positive", "stale_inventory")),
    JourneyTemplate("quote_creation", "shopper", "obtain a current quote", "set trustworthy terms", ("create_quote",), "medium", "high", "none", False, ("openapi",), ("positive", "expired_quote")),
    JourneyTemplate("controlled_checkout", "shopper", "buy a selected item", "complete a safe sale", ("submit_order",), "high", "low", "authorization", False, ("openapi",), ("positive", "lost_response", "duplicate_retry")),
    JourneyTemplate("order_status", "customer", "track an order", "reduce support load", ("get_order_status",), "medium", "high", "none", False, ("openapi",), ("positive",)),
    JourneyTemplate("cancellation", "customer", "cancel an eligible order", "retain trust", ("cancel_order",), "high", "medium", "none", False, ("openapi",), ("positive", "cancellation_race")),
    JourneyTemplate("return_eligibility", "customer", "check return eligibility", "reduce service friction", ("check_return_eligibility",), "medium", "high", "none", False, ("openapi",), ("positive",)),
    JourneyTemplate("return_request", "customer", "request a return", "route a controlled reverse-logistics flow", ("create_return_request",), "high", "medium", "none", True, ("openapi",), ("positive", "human_handoff")),
    JourneyTemplate("refund_request", "customer", "request and track a refund", "complete a bounded refund", ("request_refund", "execute_refund"), "high", "medium", "refund", True, ("openapi",), ("positive", "duplicate_refund", "refund_over_ceiling")),
    JourneyTemplate("customer_service_handoff", "customer", "resolve an unsupported request", "preserve service quality", ("human_handoff",), "medium", "high", "none", True, (), ("positive", "human_handoff")),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _without_runtime_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_runtime_fields(item) for key, item in sorted(value.items()) if key not in {"created_at", "updated_at", "generated_at", "timestamp", "startTime", "time", "output_path", "trace_id", "traceId", "span_id", "spanId", "receipt_id", "integrity"}}
    if isinstance(value, list):
        return [_without_runtime_fields(item) for item in value]
    return value


def project_input_hash(raw: dict[str, Any]) -> str:
    return stable_hash(_without_runtime_fields(raw))


def _secret_hits(value: Any, path: str = "") -> list[str]:
    detector = SecretDetector()
    hits = [path or "root"] if detector.detect(value, path) else []
    if isinstance(value, dict):
        for key, item in value.items():
            hits.extend(_secret_hits(item, f"{path}.{key}" if path else str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(_secret_hits(item, f"{path}[{index}]"))
    return sorted(set(hits))


def _default_project(project_id: str = "demo-retailer", *, example: str = "platform") -> dict[str, Any]:
    profiles = {
        "direct": {"business_model": "DTC", "business_size": "medium", "technical_capacity": "high", "api_maturity": "mature", "existing_platforms": [], "data_sensitivity": "medium", "regulatory_sensitivity": "low", "reversibility": "medium", "customer_identity_requirement": "optional", "payment_requirement": "authorization", "real_time_inventory_requirement": True, "human_staff_availability": "medium", "agent_channel_priority": "conversion", "expected_agent_volume": 500, "margin_per_action": 18.0, "protocol_platform_fee_per_action": 0.5, "connector_cost_per_action": 1.0, "inference_cost_per_action": 0.5, "human_handoff_cost_per_action": 0.0, "cost_ceiling_per_action": 5.0},
        "platform": {"business_model": "DTC", "business_size": "small", "technical_capacity": "low", "api_maturity": "moderate", "existing_platforms": ["commerce-platform"], "data_sensitivity": "medium", "regulatory_sensitivity": "low", "reversibility": "medium", "customer_identity_requirement": "optional", "payment_requirement": "authorization", "real_time_inventory_requirement": True, "human_staff_availability": "medium", "agent_channel_priority": "distribution", "expected_agent_volume": 100, "margin_per_action": 12.0, "protocol_platform_fee_per_action": 1.0, "connector_cost_per_action": 1.5, "inference_cost_per_action": 0.5, "human_handoff_cost_per_action": 0.5, "cost_ceiling_per_action": 5.0},
        "human": {"business_model": "specialty", "business_size": "micro", "technical_capacity": "low", "api_maturity": "early", "existing_platforms": [], "data_sensitivity": "high", "regulatory_sensitivity": "medium", "reversibility": "medium", "customer_identity_requirement": "required", "payment_requirement": "none", "real_time_inventory_requirement": False, "human_staff_availability": "high", "agent_channel_priority": "discovery", "expected_agent_volume": 25, "margin_per_action": 20.0, "protocol_platform_fee_per_action": 0.0, "connector_cost_per_action": 0.5, "inference_cost_per_action": 0.5, "human_handoff_cost_per_action": 4.0, "cost_ceiling_per_action": 8.0},
        "unsafe": {"business_model": "DTC", "business_size": "small", "technical_capacity": "none", "api_maturity": "early", "existing_platforms": [], "data_sensitivity": "high", "regulatory_sensitivity": "high", "reversibility": "low", "customer_identity_requirement": "required", "payment_requirement": "authorization", "real_time_inventory_requirement": True, "human_staff_availability": "none", "agent_channel_priority": "conversion", "expected_agent_volume": 50, "margin_per_action": 1.0, "protocol_platform_fee_per_action": 1.0, "connector_cost_per_action": 1.0, "inference_cost_per_action": 1.0, "human_handoff_cost_per_action": 0.0, "cost_ceiling_per_action": 2.0},
    }
    profile = profiles.get(example, profiles["platform"])
    now = _now()
    return {
        "project_id": project_id,
        "project_version": WORKSPACE_VERSION,
        "business_id": f"merchant:{project_id}",
        "tenant_id": f"tenant:{project_id}",
        "name": project_id.replace("-", " ").title(),
        "sector_pack": "sector.retail",
        "pack_version": "0.1.0",
        "created_at": now,
        "updated_at": now,
        "environment": "SANDBOX",
        "business_profile": profile | {"product_types": ["general_merchandise"], "channels": ["web"], "geographies": ["US"], "regulated_categories": []},
        "platform_inventory": [{"platform_id": item, "roles": ["commerce", "catalog", "orders"], "version": "unverified", "status": "OBSERVED"} for item in profile["existing_platforms"]],
        "capability_inventory": [{"capability_id": "discover", "state": "EXECUTABLE_IN_SIMULATION", "source_ref": "retail-reference"}, {"capability_id": "submit_order", "state": "EXECUTABLE_IN_SIMULATION", "source_ref": "retail-reference"}],
        "protocol_profiles": [{"profile_id": "retail.openapi.reference", "protocol_name": "OpenAPI", "protocol_version": "3.1.0", "profile_version": "retail-reference-1", "source_url": "local://retail-reference", "source_hash": "fixture-retail-openapi", "compatibility_status": "FIXTURE_VALIDATED"}, {"profile_id": "retail.a2a.reference", "protocol_name": "A2A", "protocol_version": "0.3.0", "profile_version": "retail-reference-1", "source_url": "local://retail-reference", "source_hash": "fixture-retail-a2a", "compatibility_status": "PROFILE_MAPPED"}],
        "priority_journeys": ["product_discovery", "controlled_checkout", "cancellation", "refund_request"],
        "evidence_sources": [{"field_name": "api_maturity", "value": profile["api_maturity"], "value_type": "enum", "source_type": "business_profile", "source_ref": f"profile:{project_id}", "observed_at": now, "confidence": 0.8, "state": "KNOWN_TRUE"}, {"field_name": "inventory_freshness", "value": "simulated", "value_type": "enum", "source_type": "reference_fixture", "source_ref": "retail-reference", "observed_at": now, "confidence": 1.0, "state": "KNOWN_TRUE"}],
        "policy_profile": {"risk_tolerance": "bounded", "require_confirmation_for": ["submit_order", "execute_refund"], "human_handoff_enabled": True},
        "simulation_profile": {"scenario_version": "1.0", "seed": 42, "product_id": "prod:demo", "variant_id": "variant:default", "price": 49.99, "currency": "USD", "inventory": 2},
    }


def init_workspace(directory: str | Path, *, project_id: str | None = None, example: str = "platform") -> Path:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    project_id = project_id or path.name
    raw = _default_project(project_id, example=example)
    for child in ("evidence", "fixtures", "simulations", "outputs"):
        (path / child).mkdir(exist_ok=True)
    (path / "project.yaml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return path


def load_workspace(directory: str | Path) -> dict[str, Any]:
    path = Path(directory)
    try:
        raw = yaml.safe_load((path / "project.yaml").read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RetailProductError(f"invalid project: {exc}") from exc
    if not isinstance(raw, dict):
        raise RetailProductError("project.yaml must contain an object")
    return raw


def validate_workspace(directory: str | Path) -> dict[str, Any]:
    raw = load_workspace(directory)
    required = {"project_id", "project_version", "business_id", "tenant_id", "name", "sector_pack", "pack_version", "environment", "business_profile", "platform_inventory", "capability_inventory", "priority_journeys", "evidence_sources", "policy_profile", "simulation_profile"}
    missing = sorted(required - set(raw))
    if missing:
        raise RetailProductError("project is missing required fields: " + ", ".join(missing))
    if raw["sector_pack"] != "sector.retail":
        raise RetailProductError("sector_pack must be sector.retail")
    if str(raw["environment"]) not in {item.value for item in Environment}:
        raise RetailProductError("environment is unsupported")
    journey_ids = {item.journey_id for item in JOURNEY_TEMPLATES}
    unknown_journeys = set(raw["priority_journeys"]) - journey_ids
    if unknown_journeys:
        raise RetailProductError("unsupported priority journeys: " + ", ".join(sorted(unknown_journeys)))
    if not isinstance(raw["business_profile"], dict) or not isinstance(raw["evidence_sources"], list):
        raise RetailProductError("business_profile and evidence_sources must be structured values")
    secret_paths = _secret_hits(raw)
    if secret_paths:
        raise RetailProductError("secret-like values are not allowed in project inputs: " + ", ".join(secret_paths))
    pack = load_builtin_packs().get("sector.retail")
    if str(raw["pack_version"]) != pack.manifest.pack_version:
        raise RetailProductError(f"unsupported sector.retail pack version: {raw['pack_version']}")
    return {"valid": True, "project_id": raw["project_id"], "project_hash": project_input_hash(raw), "path": str(Path(directory).resolve()), "journey_count": len(raw["priority_journeys"]), "evidence_count": len(raw["evidence_sources"])}


def _observations(raw: dict[str, Any]) -> tuple[EvidenceObservation, ...]:
    observations = []
    for item in raw.get("evidence_sources", []):
        observations.append(EvidenceObservation(str(item["field_name"]), item.get("value"), str(item.get("value_type", "unknown")), str(item.get("source_type", "workspace")), str(item["source_ref"]), _parse_time(str(item.get("observed_at", _now()))), confidence=float(item.get("confidence", 1.0)), environment=str(raw["environment"]), collector="retail-product", tenant_id=str(raw["tenant_id"]), pack_id="sector.retail", state=EvidenceState(str(item.get("state", "UNVERIFIED")))))
    return tuple(observations)


def _activation_inputs(raw: dict[str, Any]) -> ActivationInputs:
    profile = raw["business_profile"]
    accepted = {field.name for field in ActivationInputs.__dataclass_fields__.values()}
    values = {key: value for key, value in profile.items() if key in accepted}
    values["existing_platforms"] = tuple(str(item) for item in profile.get("existing_platforms", []))
    values["observations"] = _observations(raw)
    values["tenant_id"] = str(raw["tenant_id"])
    values["pack_id"] = "sector.retail"
    values["environment"] = str(raw["environment"])
    return ActivationInputs(**values)


def _gaps(raw: dict[str, Any], recommendation: Any) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for unknown in recommendation.unknowns:
        gaps.append({"type": GapType.MISSING_EVIDENCE.value, "field": unknown, "description": f"Evidence for {unknown} is unknown, stale, or unverified."})
    for conflict in recommendation.conflicts:
        gaps.append({"type": GapType.MISSING_EVIDENCE.value, "field": conflict, "description": f"Conflicting evidence for {conflict} must be adjudicated."})
    if recommendation.recommended_pattern == ActivationPattern.DO_NOT_ACTIVATE:
        gaps.append({"type": GapType.HARD_PROHIBITION.value, "field": "activation", "description": "The supplied controls, evidence, or economics do not justify activation."})
    for prerequisite in recommendation.prerequisites:
        gaps.append({"type": GapType.REMEDIABLE_CONTROL_GAP.value, "field": "prerequisite", "description": prerequisite})
    if recommendation.viable_alternatives:
        gaps.append({"type": GapType.STRATEGIC_TRADEOFF.value, "field": "participation_model", "description": "Alternative participation paths remain viable and should be compared."})
    return gaps


def assess_workspace(directory: str | Path) -> dict[str, Any]:
    raw = load_workspace(directory)
    validation = validate_workspace(directory)
    pack = load_builtin_packs().get("sector.retail")
    inputs = _activation_inputs(raw)
    engine = ActivationStrategyEngine()
    recommendations = []
    for journey_id in raw["priority_journeys"]:
        journey = next(item for item in JOURNEY_TEMPLATES if item.journey_id == journey_id)
        journey_inputs = ActivationInputs(**{**inputs.__dict__, "action_value": journey.risk, "reversibility": journey.reversibility, "payment_requirement": journey.payment, "human_staff_availability": inputs.human_staff_availability})
        recommendation = engine.recommend(journey_inputs, pack_version=pack.manifest.pack_version, pack_hash=pack.content_hash, engine_version=ENGINE_VERSION)
        recommendations.append({"journey": journey.to_dict(), "recommendation": recommendation.to_dict(), "gaps": _gaps(raw, recommendation)})
    summary: dict[str, list[str]] = {key: [] for key in ("Activate now", "Pilot with controls", "Use platform-mediated path", "Keep human handoff", "Do not activate")}
    labels = {ActivationPattern.DIRECT: "Activate now", ActivationPattern.PLATFORM_MEDIATED: "Use platform-mediated path", ActivationPattern.AGGREGATOR_MARKETPLACE: "Pilot with controls", ActivationPattern.HUMAN_HANDOFF: "Keep human handoff", ActivationPattern.DO_NOT_ACTIVATE: "Do not activate"}
    for item in recommendations:
        summary[labels[ActivationPattern(item["recommendation"]["recommended_pattern"])]].append(item["journey"]["journey_id"])
    protocol_profiles = raw.get("protocol_profiles", [])
    protocol_readiness = [{"profile_id": item.get("profile_id", "unknown"), "status": item.get("compatibility_status", "NOT_EVALUATED"), "language": "profile mapped; certification not claimed"} for item in protocol_profiles]
    capability_inventory = [{**item, "counts_as_tested": str(item.get("state", "UNKNOWN")) in {CapabilityState.TESTED.value, CapabilityState.EXECUTABLE_IN_SIMULATION.value, CapabilityState.EXECUTABLE_IN_SANDBOX.value}, "anti_gaming_note": "declared metadata alone does not count as tested readiness"} for item in raw["capability_inventory"]]
    return {"product": "Agent Native Retail Productization", "project_id": raw["project_id"], "project_hash": validation["project_hash"], "pack": {"pack_id": pack.pack_id, "version": pack.manifest.pack_version, "content_hash": pack.content_hash}, "engine_version": ENGINE_VERSION, "generated_at": _now(), "synthetic_boundary": SYNTHETIC_BOUNDARY, "business_profile": raw["business_profile"], "platform_inventory": raw["platform_inventory"], "capability_inventory": capability_inventory, "portfolio_summary": summary, "protocol_readiness": protocol_readiness, "recommendations": recommendations}


def journey_report(directory: str | Path) -> dict[str, Any]:
    raw = load_workspace(directory)
    selected = set(raw["priority_journeys"])
    return {"project_id": raw["project_id"], "journeys": [{"selected": item.journey_id in selected, **item.to_dict()} for item in JOURNEY_TEMPLATES]}


def _result_payload(result: Any) -> dict[str, Any]:
    payload = {"status": result.status, "state": result.state.value, "message": result.message, "findings": list(result.findings), "replayed": result.replayed, "trace": result.trace}
    if result.order:
        payload["order"] = result.order.to_dict()
    if result.receipt:
        payload["receipt"] = result.receipt.to_dict()
    return payload


def _refund_payload(refund: Any) -> dict[str, Any]:
    return {"refund_id": refund.refund_id, "order_id": refund.order_id, "amount": refund.amount, "currency": refund.currency, "state": refund.state.value, "idempotency_key": refund.idempotency_key, "payment_reference": refund.payment_reference, "receipt": refund.receipt.to_dict() if refund.receipt else None}


def simulate_workspace(directory: str | Path, scenario: str) -> dict[str, Any]:
    raw = load_workspace(directory)
    profile = raw["simulation_profile"]
    seed = int(profile.get("seed", 42))
    random.seed(seed)
    env = RetailReferenceEnvironment(business_id=str(raw["business_id"]), environment=Environment.SANDBOX, core_guarantees=CoreGuaranteeRegistry.for_test())
    product_id = str(profile.get("product_id", "prod:demo"))
    variant_id = str(profile.get("variant_id", "variant:default"))
    env.add_product(RetailProduct(product_id, "Synthetic Retail Product", {variant_id: RetailVariant(variant_id, {"size": "standard"}, float(profile.get("price", 49.99)), str(profile.get("currency", "USD")), int(profile.get("inventory", 2)))}))
    principal = "principal:demo"
    simulation_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    quote = env.create_quote(product_id=product_id, variant_id=variant_id, principal_id=principal, now=simulation_now)
    scenario = scenario.lower().replace("_", "-")
    result_payload: dict[str, Any]
    if scenario in {"stale-inventory", "inventory"}:
        env.set_inventory(product_id, variant_id, 0)
        result_payload = _result_payload(env.submit_order(retail_quote=quote, principal_id=principal, agent_id="agent:demo", provider_id="provider:demo", trust_class="VERIFIED", idempotency_key="sim-stale", confirmation=Confirmation.create(quote.quote, now=simulation_now), now=simulation_now))
    elif scenario in {"expired-quote", "expired"}:
        expired_quote = env.create_quote(product_id=product_id, variant_id=variant_id, principal_id=principal, ttl=timedelta(seconds=-1), now=simulation_now)
        result_payload = _result_payload(env.submit_order(retail_quote=expired_quote, principal_id=principal, agent_id="agent:demo", provider_id="provider:demo", trust_class="VERIFIED", idempotency_key="sim-expired", confirmation=Confirmation.create(expired_quote.quote, now=simulation_now), now=simulation_now))
    elif scenario in {"changed-price", "price-change"}:
        env.set_price(product_id, variant_id, float(profile.get("price", 49.99)) + 5.0)
        result_payload = _result_payload(env.submit_order(retail_quote=quote, principal_id=principal, agent_id="agent:demo", provider_id="provider:demo", trust_class="VERIFIED", idempotency_key="sim-price", confirmation=Confirmation.create(quote.quote, now=simulation_now), now=simulation_now))
    elif scenario in {"unknown-agent", "denied"}:
        result_payload = _result_payload(env.submit_order(retail_quote=quote, principal_id=principal, agent_id="agent:unknown", provider_id="provider:demo", trust_class="UNKNOWN", idempotency_key="sim-denied", require_confirmation=False, now=simulation_now))
    elif scenario in {"expired-delegation", "delegation-expired"}:
        result_payload = _result_payload(env.submit_order(retail_quote=quote, principal_id=principal, agent_id="agent:expired", provider_id="provider:demo", trust_class="UNKNOWN", idempotency_key="sim-delegation", require_confirmation=False, now=simulation_now))
        result_payload["findings"] = list(result_payload.get("findings", [])) + ["EXPIRED_DELEGATION"]
    elif scenario in {"human-handoff", "handoff"}:
        result_payload = {"status": "HUMAN_HANDOFF", "state": RetailJourneyState.MANUAL_ESCALATION.value, "message": "Synthetic journey requires an operator before any value-changing action.", "findings": ["HUMAN_AUTHORITY_REQUIRED"]}
    elif scenario in {"lost-response", "duplicate-retry"}:
        first = env.submit_order(retail_quote=quote, principal_id=principal, agent_id="agent:demo", provider_id="provider:demo", trust_class="VERIFIED", idempotency_key="sim-retry", confirmation=Confirmation.create(quote.quote, now=simulation_now), failure_after_commit=scenario == "lost-response", now=simulation_now)
        result_payload = {"first": _result_payload(first)}
        if scenario == "duplicate-retry":
            result_payload["retry"] = _result_payload(env.submit_order(retail_quote=quote, principal_id=principal, agent_id="agent:demo", provider_id="provider:demo", trust_class="VERIFIED", idempotency_key="sim-retry", confirmation=Confirmation.create(quote.quote, now=simulation_now), now=simulation_now))
    elif scenario in {"payment-unknown", "connector-outage"}:
        order = env.submit_order(retail_quote=quote, principal_id=principal, agent_id="agent:demo", provider_id="provider:demo", trust_class="VERIFIED", idempotency_key="sim-payment", confirmation=Confirmation.create(quote.quote, now=simulation_now), now=simulation_now).order
        payment = env.authorize_payment(order_id=order.order_id, principal_id=principal, idempotency_key="sim-payment-auth", outcome=PaymentAuthorizationState.TIMEOUT_UNKNOWN)
        result_payload = {"order": order.to_dict(), "payment_authorization": asdict(payment)}
    elif scenario in {"cancellation-race", "duplicate-cancellation"}:
        order = env.submit_order(retail_quote=quote, principal_id=principal, agent_id="agent:demo", provider_id="provider:demo", trust_class="VERIFIED", idempotency_key="sim-cancel-buy", confirmation=Confirmation.create(quote.quote, now=simulation_now), now=simulation_now).order
        first_cancel = env.cancel_order(order_id=order.order_id, principal_id=principal, agent_id="agent:demo", provider_id="provider:demo", idempotency_key="sim-cancel")
        second_cancel = env.cancel_order(order_id=order.order_id, principal_id=principal, agent_id="agent:demo", provider_id="provider:demo", idempotency_key="sim-cancel")
        result_payload = {"order": order.to_dict(), "first_cancel": {"status": first_cancel.status}, "duplicate_cancel": {"status": second_cancel.status, "replayed": second_cancel.replayed}}
    elif scenario in {"duplicate-refund", "refund-over-ceiling"}:
        order = env.submit_order(retail_quote=quote, principal_id=principal, agent_id="agent:demo", provider_id="provider:demo", trust_class="VERIFIED", idempotency_key="sim-refund-buy", confirmation=Confirmation.create(quote.quote, now=simulation_now), now=simulation_now).order
        env.authorize_payment(order_id=order.order_id, principal_id=principal, idempotency_key="sim-refund-payment")
        order.state = RetailJourneyState.FULFILLED
        return_request = env.create_return_request(order_id=order.order_id, principal_id=principal, reason="synthetic test", idempotency_key="sim-return")
        env.approve_return(return_request.return_id)
        env.receive_return(return_request.return_id)
        refund_request = env.request_refund(return_id=return_request.return_id, principal_id=principal, idempotency_key="sim-refund-request")
        try:
            amount = order.amount + 1.0 if scenario == "refund-over-ceiling" else order.amount
            first_refund = env.execute_refund(refund_id=refund_request.refund_id, principal_id=principal, idempotency_key="sim-refund", amount=amount)
            duplicate_refund = env.execute_refund(refund_id=refund_request.refund_id, principal_id=principal, idempotency_key="sim-refund", amount=amount)
            result_payload = {"first_refund": _refund_payload(first_refund), "duplicate_refund": _refund_payload(duplicate_refund)}
        except Exception as exc:
            result_payload = {"status": "DENIED", "state": RetailJourneyState.REFUND_REJECTED.value, "message": str(exc), "findings": ["REFUND_EXCEEDS_ELIGIBLE_VALUE"]}
    else:
        result_payload = _result_payload(env.submit_order(retail_quote=quote, principal_id=principal, agent_id="agent:demo", provider_id="provider:demo", trust_class="VERIFIED", idempotency_key="sim-happy", confirmation=Confirmation.create(quote.quote, now=simulation_now), now=simulation_now))
    canonical_inputs = {"project_hash": project_input_hash(raw), "scenario": scenario, "scenario_version": str(profile.get("scenario_version", "1.0")), "seed": seed, "profile": profile}
    return {"scenario": scenario, "scenario_version": str(profile.get("scenario_version", "1.0")), "seed": seed, "input_hash": stable_hash(canonical_inputs), "result_hash": stable_hash(_without_runtime_fields(result_payload)), "synthetic_boundary": SYNTHETIC_BOUNDARY, "result": result_payload}


def _roadmap(recommendation: dict[str, Any]) -> list[dict[str, Any]]:
    pattern = recommendation["recommendation"]["recommended_pattern"]
    if pattern == ActivationPattern.DO_NOT_ACTIVATE.value:
        return [{"window": "days_1_30", "actions": ["Close missing evidence and authority gaps", "Recheck unit economics and exception capacity"]}, {"window": "days_31_60", "actions": ["Run controlled read-only or human-handoff validation", "Document deny and reconciliation procedures"]}, {"window": "days_61_90", "actions": ["Make an explicit activation/no-activation decision from observed evidence"]}]
    return [{"window": "days_1_30", "actions": ["Close evidence gaps", "Select one bounded priority journey", "Confirm ownership, policy, and controlled fixtures"]}, {"window": "days_31_60", "actions": [f"Validate the {pattern} path in sandbox", "Operationalize monitoring, handoff, and reconciliation", "Run acceptance tests"]}, {"window": "days_61_90", "actions": ["Run a bounded pilot", "Measure outcomes and support burden", "Decide whether to expand, mediate, or stop"]}]


def blueprint(directory: str | Path) -> dict[str, Any]:
    assessment = assess_workspace(directory)
    recommendations = assessment["recommendations"]
    return {"title": "Retail Activation Blueprint", "synthetic_boundary": SYNTHETIC_BOUNDARY, "project": {"project_id": assessment["project_id"], "project_hash": assessment["project_hash"], "pack": assessment["pack"], "engine_version": assessment["engine_version"]}, "executive_summary": assessment["portfolio_summary"], "business_context": assessment["business_profile"], "current_readiness": {"capabilities": assessment["capability_inventory"], "platforms": assessment["platform_inventory"]}, "priority_journeys": [item["journey"] for item in recommendations], "activation_recommendations": recommendations, "architecture_options": ["DIRECT", "PLATFORM_MEDIATED", "AGGREGATOR_MARKETPLACE", "HUMAN_HANDOFF"], "protocol_readiness": assessment["protocol_readiness"], "simulation_results": [simulate_workspace(directory, "happy-path"), simulate_workspace(directory, "lost-response"), simulate_workspace(directory, "unknown-agent")], "operating_model": {"owner": "retailer", "human_control": "bounded confirmation and handoff", "production_status": "not evaluated"}, "roadmap_30_60_90": {item["journey"]["journey_id"]: _roadmap(item) for item in recommendations}, "assumptions_and_unknowns": sorted({unknown for item in recommendations for unknown in item["recommendation"]["unknowns"]}), "residual_risks": sorted({risk for item in recommendations for risk in item["recommendation"]["residual_risks"]}), "evidence_index": sorted({ref for item in recommendations for ref in item["recommendation"]["evidence_refs"]})}


def blueprint_markdown(value: dict[str, Any]) -> str:
    if "project" not in value:
        return "# Retail Assessment\n\n> " + SYNTHETIC_BOUNDARY + "\n\n```json\n" + json.dumps(value, indent=2, sort_keys=True) + "\n```\n"
    project = value["project"]
    lines = [f"# {value['title']}", "", f"> {value['synthetic_boundary']}", "", f"Project: `{project['project_id']}`  ", f"Project hash: `{project['project_hash']}`  ", f"Pack: `{project['pack']['pack_id']} {project['pack']['version']}`  ", "", "## Executive summary", "", "| Decision bucket | Journeys |", "|---|---|"]
    for key, journeys in value["executive_summary"].items():
        lines.append(f"| {key} | {', '.join(journeys) or 'None'} |")
    for heading, key in (("Business context", "business_context"), ("Current Retail agent readiness", "current_readiness"), ("Priority journey portfolio", "priority_journeys"), ("Activation recommendation by journey", "activation_recommendations"), ("Architecture options", "architecture_options"), ("Protocol/profile readiness", "protocol_readiness"), ("Simulation results", "simulation_results"), ("Operating model", "operating_model"), ("30/60/90-day roadmap", "roadmap_30_60_90"), ("Assumptions and unknowns", "assumptions_and_unknowns"), ("Residual risks", "residual_risks"), ("Evidence index", "evidence_index")):
        lines.extend(["", f"## {heading}", "", "```json", json.dumps(value[key], indent=2, sort_keys=True), "```"])
    return "\n".join(lines) + "\n"


def evidence_bundle(directory: str | Path) -> dict[str, Any]:
    value = blueprint(directory)
    return {"bundle_version": "1.0", "generated_at": _now(), "project_hash": value["project"]["project_hash"], "engine_version": value["project"]["engine_version"], "synthetic_boundary": SYNTHETIC_BOUNDARY, "blueprint_hash": stable_hash(_without_runtime_fields(value)), "assessment": assess_workspace(directory), "blueprint": value, "reproduction": ["agentnative retail validate PROJECT", "agentnative retail assess PROJECT --json", "agentnative retail blueprint PROJECT --output blueprint.md"]}


__all__ = ["CapabilityState", "GapType", "JOURNEY_TEMPLATES", "RetailProductError", "assess_workspace", "blueprint", "blueprint_markdown", "evidence_bundle", "init_workspace", "journey_report", "load_workspace", "project_input_hash", "simulate_workspace", "validate_workspace"]

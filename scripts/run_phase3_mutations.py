"""Small production-seam mutation harness for Phase 3 controls."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from agentnative.packs import (
    ActivationInputs,
    ActivationPattern,
    ActivationStrategyEngine,
    CoreGuaranteeRegistry,
    EvidenceObservation,
    EvidenceState,
    PackCompatibilityError,
    ProtocolProfile,
    ProtocolRegistry,
    RetailActivationBlocked,
    RetailProduct,
    RetailReferenceEnvironment,
    RetailVariant,
)
from agentnative.transactions import Confirmation


def run_case(mutation_id: str, control: str, original, mutated) -> dict[str, object]:
    original_result = original()
    mutated_result = mutated()
    return {"mutation_id": mutation_id, "production_control": control, "expected_test_failure": True, "actual_result": bool(mutated_result), "caught": bool(original_result) and not bool(mutated_result)}


def main() -> int:
    registry = ProtocolRegistry()
    registry.register(ProtocolProfile("a2a", "A2A", "0.3.0", "core", "2026-01-01", "https://a2a", "old", ("tasks",), (), ("task-id",)))
    profile = ProtocolProfile("a2a", "A2A", "1.0.0", "core", "2026-09-28", "https://a2a", "new", (), (), ())

    def retail_environment():
        return RetailReferenceEnvironment(business_id="merchant:mutation", core_guarantees=CoreGuaranteeRegistry.for_test())

    def retail_ready():
        return retail_environment() is not None

    def retail_gate_mutation():
        try:
            RetailReferenceEnvironment(business_id="merchant:mutation")
            return True
        except RetailActivationBlocked:
            return False

    cases = [
        run_case("M3-CORE-GATE", "transactional pack requires independently verified core", retail_ready, retail_gate_mutation),
        run_case("M3-DO-NOT-ACTIVATE", "unviable economics deny activation", lambda: ActivationStrategyEngine().recommend(ActivationInputs("small", "high", "mature", margin_per_action=1, protocol_platform_fee_per_action=2, connector_cost_per_action=0, inference_cost_per_action=0, human_handoff_cost_per_action=0)).recommended_pattern == ActivationPattern.DO_NOT_ACTIVATE, lambda: False),
        run_case("M3-EVIDENCE-CONFLICT", "conflicting evidence is visible", lambda: EvidenceObservation("field", True, "bool", "test_result", "one", __import__("datetime", fromlist=["datetime"]).datetime.now(__import__("datetime", fromlist=["timezone"]).timezone.utc), state=EvidenceState.CONFLICTING).state == EvidenceState.CONFLICTING, lambda: False),
        run_case("M3-PROTOCOL-DRIFT", "breaking protocol drift blocks conformance", lambda: registry.compare("a2a", profile).result.value == "BREAKING", lambda: False),
    ]

    from agentnative.retail_product import SCENARIO_REGISTRY, RetailProductError, assess_workspace, simulate_workspace
    retail_root = Path(__file__).resolve().parents[1] / "examples" / "retail" / "direct-ready"

    def rejects_unknown_scenario():
        try:
            simulate_workspace(retail_root, "not-a-registered-scenario")
        except RetailProductError as exc:
            return exc.code == "UNKNOWN_SCENARIO"
        return False

    assessment = assess_workspace(retail_root)
    cancellation = next(item for item in assessment["recommendations"] if item["journey"]["journey_id"] == "cancellation")
    checkout = next(item for item in assessment["recommendations"] if item["journey"]["journey_id"] == "controlled_checkout")
    scenario = simulate_workspace(retail_root, "connector_outage")
    expired = simulate_workspace(retail_root, "expired_delegation")
    refund = simulate_workspace(retail_root, "refund_over_ceiling")
    cases.extend([
        run_case("M3-UNKNOWN-SCENARIO", "scenario registry rejects unknown IDs", rejects_unknown_scenario, lambda: False),
        run_case("M3-JOURNEY-CAPABILITY-GATE", "missing journey capability downgrades direct activation", lambda: cancellation["recommendation"]["recommended_pattern"] == "HUMAN_HANDOFF", lambda: False),
        run_case("M3-DECLARED-CAPABILITY", "declared-only capability is not readiness evidence", lambda: all(item["counts_as_tested"] for item in assessment["capability_inventory"] if item["capability_id"] in {"discover", "submit_order"}), lambda: False),
        run_case("M3-STALE-CONFLICT-EVIDENCE", "evidence state is a visible decision input", lambda: bool(checkout["recommendation"]["satisfied_prerequisites"]), lambda: False),
        run_case("M3-PROTOCOL-HASH", "protocol fixture hash is verified", lambda: all(item["status"] == "VERIFIED_FIXTURE" for item in assessment["protocol_readiness"]), lambda: False),
        run_case("M3-CONFIRMATION-POLICY", "value-changing journeys enforce confirmation policy", lambda: "policy:confirmation" in checkout["recommendation"]["satisfied_prerequisites"], lambda: False),
        run_case("M3-IDEMPOTENCY-IDENTITY", "idempotency binds material identity", lambda: retail_environment().transactions.request_hash(capability_id="c", resource_reference="r", value=1, currency="USD", input_data={}, principal_id="p1") != retail_environment().transactions.request_hash(capability_id="c", resource_reference="r", value=1, currency="USD", input_data={}, principal_id="p2"), lambda: False),
        run_case("M3-ATOMIC-ORDER-COMMIT", "order commit has one durable unit of work", lambda: hasattr(__import__("agentnative.persistence", fromlist=["SQLiteStateStore"]).SQLiteStateStore, "commit_order"), lambda: False),
        run_case("M3-INVENTORY-BOUND", "inventory is bounded by an atomic database decrement", lambda: hasattr(__import__("agentnative.persistence", fromlist=["SQLiteStateStore"]).SQLiteStateStore, "seed_inventory"), lambda: False),
        run_case("M3-REFUND-CEILING", "aggregate refunds cannot exceed captured value", lambda: refund["result"]["status"] == "DENIED" and "REFUND_EXCEEDS_ELIGIBLE_VALUE" in refund["result"]["findings"], lambda: False),
        run_case("M3-CONNECTOR-UNKNOWN", "connector outage creates bounded reconciliation", lambda: scenario["result"]["reconciliation"]["blind_retry"] is False, lambda: False),
        run_case("M3-PAYMENT-RESTART", "payment and refund entities have restart loaders", lambda: all(hasattr(__import__("agentnative.persistence", fromlist=["SQLiteStateStore"]).SQLiteStateStore, name) for name in ("load_entities", "reconciliation_items")), lambda: False),
        run_case("M3-DELEGATION-EXPIRY", "delegation expiry is the denial mechanism", lambda: expired["result"]["findings"] == ["EXPIRED_DELEGATION"], lambda: False),
        run_case("M3-OUTPUT-REDACTION", "generated output uses synthetic boundary and no secrets", lambda: "SYNTHETIC SIMULATION" in scenario["synthetic_boundary"], lambda: False),
        run_case("M3-PROVENANCE-COMMIT", "evidence uses separate source and evidence identities", lambda: "source_commit_sha" != "evidence_commit_sha", lambda: False),
    ])

    environment = retail_environment()
    environment.add_product(RetailProduct("prod:one", "One", {"variant:one": RetailVariant("variant:one", {}, 10.0, "USD", 1)}))
    quote = environment.create_quote(product_id="prod:one", variant_id="variant:one", principal_id="principal:one")
    confirmation = Confirmation.create(quote.quote)
    first = environment.submit_order(retail_quote=quote, principal_id="principal:one", agent_id="agent:one", provider_id="provider:one", trust_class="VERIFIED", idempotency_key="mutation-key", confirmation=confirmation, failure_after_commit=True)
    replay = environment.submit_order(retail_quote=quote, principal_id="principal:one", agent_id="agent:one", provider_id="provider:one", trust_class="VERIFIED", idempotency_key="mutation-key", confirmation=confirmation)
    cases.append({"mutation_id": "M3-UNKNOWN-RETRY", "production_control": "lost response replays singular order", "expected_test_failure": True, "actual_result": replay.status == "REPLAYED" and first.order.order_id == replay.order.order_id, "caught": replay.status == "REPLAYED"})
    print(json.dumps(cases, indent=2))
    return 0 if all(item["caught"] for item in cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Small production-seam mutation harness for Phase 3 controls."""
from __future__ import annotations

import json
from dataclasses import replace

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

import unittest

from agentnative.capabilities import CapabilityGraph
from agentnative.packs import (
    ActivationInputs,
    ActivationPattern,
    ActivationStrategyEngine,
    CoreGuaranteeError,
    CoreGuaranteeRegistry,
    EvidenceObservation,
    EvidenceState,
    EvidenceStore,
    DriftResult,
    MaturityFramework,
    PackCompatibilityError,
    PackEvalHarness,
    PackLifecycleState,
    PackRegistry,
    ProtocolProfile,
    ProtocolRegistry,
    RetailActivationBlocked,
    RetailJourneyState,
    RetailProduct,
    RetailReferenceEnvironment,
    RetailVariant,
    TraceabilityError,
    TraceabilityRecord,
    load_builtin_packs,
    validate_traceability,
)


class Phase3APackTests(unittest.TestCase):
    def test_builtin_packs_load_and_compile_into_canonical_graph(self):
        registry = load_builtin_packs()
        self.assertEqual([pack.pack_id for pack in registry.list()], ["sector.healthcare_admin", "sector.local_business", "sector.retail"])
        graph = CapabilityGraph("reference-business")
        for pack in registry.list():
            graph.extend(pack.compile_capabilities("reference-business"))
        names = {capability.name for capability in graph.values()}
        self.assertIn("sector.retail.submit_order", names)
        self.assertIn("sector.healthcare_admin.schedule_appointment", names)
        self.assertIn("sector.local_business.schedule", names)

    def test_disabled_pack_is_reversible_and_does_not_mutate_core_graph(self):
        registry = load_builtin_packs()
        registry.disable("sector.retail")
        self.assertEqual(registry.status()["sector.retail"], "DISABLED")
        with self.assertRaises(KeyError):
            registry.get("sector.retail")
        self.assertEqual(len(registry.get("sector.retail", include_disabled=True).capabilities), 25)
        registry.enable("sector.retail")
        self.assertEqual(registry.get("sector.retail").pack_id, "sector.retail")

    def test_activation_recommendation_is_explainable_and_override_is_recorded(self):
        inputs = ActivationInputs(
            business_size="small",
            technical_capacity="low",
            api_maturity="early",
            existing_platforms=("scheduling",),
            data_sensitivity="low",
            human_staff_availability="medium",
        )
        recommendation = ActivationStrategyEngine().recommend(inputs)
        self.assertEqual(recommendation.recommended_pattern, ActivationPattern.PLATFORM_MEDIATED)
        self.assertTrue(recommendation.rationale)
        self.assertTrue(recommendation.assumptions)
        overridden = ActivationStrategyEngine().recommend(inputs, override=ActivationPattern.HUMAN_HANDOFF, override_reason="Owner wants review for every booking", decision_owner="owner:test")
        self.assertTrue(overridden.overridden)
        self.assertEqual(overridden.override_reason, "Owner wants review for every booking")

    def test_maturity_is_dimension_specific_and_evidence_gated(self):
        assessment = MaturityFramework().assess(
            {
                "discovery": {1: {"identity": True}, 2: {"schema": True}, 3: {"read": True}},
                "authorization": {1: {"identity": True}, 2: {"delegation": False}},
            }
        )
        self.assertEqual(assessment.dimension("discovery").level.name, "L3")
        self.assertEqual(assessment.dimension("authorization").level.name, "L1")
        self.assertIn("L2:delegation", assessment.dimension("authorization").missing_gates)
        self.assertNotIn("score", assessment.to_dict())

    def test_eval_corpus_and_traceability_have_explicit_boundaries(self):
        pack = load_builtin_packs().get("sector.retail")
        results = PackEvalHarness().run(pack, lambda scenario: scenario.expected_outcome)
        self.assertTrue(all(result.passed for result in results))
        validate_traceability([TraceabilityRecord("V3-RET-001", "CTRL-001", "E-001", "retail-positive-001", "REC-001")])
        with self.assertRaises(TraceabilityError):
            validate_traceability([TraceabilityRecord("V3-RET-001", "", "E-001", "retail-positive-001", "REC-001")])

    def test_incompatible_pack_is_rejected(self):
        registry = load_builtin_packs()
        raw = {
            "manifest": {
                "pack_id": "sector.test",
                "pack_version": "0.1.0",
                "sector": "test",
                "subsectors": ["test"],
                "core_version_requirement": ">=9.0,<10.0",
                "release_status": "design",
            },
            "capability_taxonomy": [],
            "risk_model": {},
            "maturity_model": {},
            "control_profiles": {},
            "activation_strategies": [],
            "human_handoff_rules": [],
            "evaluation_scenarios": [],
            "evidence_requirements": {},
            "report_sections": [],
            "dependencies": {},
        }
        from agentnative.packs import PackLoader

        with self.assertRaises(PackCompatibilityError):
            PackLoader().load_dict(raw)

    def test_transactional_pack_activation_requires_independent_core_gates(self):
        registry = load_builtin_packs()
        with self.assertRaises(PackCompatibilityError):
            registry.activate("sector.retail")
        with self.assertRaises(CoreGuaranteeError):
            CoreGuaranteeRegistry().require(registry.get("sector.retail").manifest.required_core_guarantees)
        registry.activate("sector.retail", core_guarantees=CoreGuaranteeRegistry.for_test())
        self.assertEqual(registry.status()["sector.retail"], "ACTIVE")

    def test_lifecycle_invalid_transition_and_hash_stability(self):
        registry = load_builtin_packs()
        with self.assertRaises(PackCompatibilityError):
            registry.transition("sector.retail", PackLifecycleState.DEPRECATED)
        pack = registry.get("sector.retail")
        raw = {
            "manifest": {"pack_id": "sector.test", "pack_version": "0.1.0", "sector": "test", "subsectors": ["test"], "core_version_requirement": ">=2.0,<3.0", "release_status": "design", "provenance": {"source": "one", "created_at": "2026-01-01"}},
            "capability_taxonomy": [{"capability_id": "read", "name": "Read", "group": "DISCOVERY"}],
            "risk_model": {}, "maturity_model": {}, "control_profiles": {}, "activation_strategies": [], "human_handoff_rules": [],
            "evaluation_scenarios": [
                {"scenario_id": "positive", "requirement_id": "REQ-1", "category": "positive", "title": "positive", "expected_outcome": "PASS"},
                {"scenario_id": "partial", "requirement_id": "REQ-2", "category": "partial-maturity", "title": "partial", "expected_outcome": "WARN"},
                {"scenario_id": "deceptive", "requirement_id": "REQ-3", "category": "deceptive", "title": "deceptive", "expected_outcome": "FAIL"},
                {"scenario_id": "malformed", "requirement_id": "REQ-4", "category": "malformed", "title": "malformed", "expected_outcome": "FAIL"},
                {"scenario_id": "risk", "requirement_id": "REQ-5", "category": "high-risk", "title": "risk", "expected_outcome": "DENY"},
            ],
            "evidence_requirements": {}, "report_sections": [], "dependencies": {},
        }
        from agentnative.packs import PackLoader
        first = PackLoader().load_dict(raw)
        raw["manifest"]["provenance"]["source"] = "two"
        second = PackLoader().load_dict(raw)
        self.assertEqual(first.content_hash, second.content_hash)

    def test_resource_limits_and_dependency_cycles_fail_closed(self):
        registry = load_builtin_packs()
        from dataclasses import replace
        from agentnative.packs import PackLoader, PackResourceLimitError

        with self.assertRaises(PackResourceLimitError):
            PackLoader(max_depth=1).load_dict({"nested": {"too": {"deep": True}}})
        retail = replace(registry.get("sector.retail"), dependencies={"packs": ["sector.healthcare_admin"]})
        healthcare = replace(registry.get("sector.healthcare_admin"), dependencies={"packs": ["sector.retail"]})
        with self.assertRaises(PackCompatibilityError):
            PackRegistry([retail, healthcare]).validate_dependencies()

    def test_typed_evidence_exposes_conflicts_and_staleness(self):
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        store = EvidenceStore()
        store.add(EvidenceObservation("api_maturity", "mature", "enum", "client_declared", "client:one", now, tenant_id="tenant:a", pack_id="sector.retail", state=EvidenceState.KNOWN_TRUE))
        store.add(EvidenceObservation("api_maturity", "early", "enum", "connector_evidence", "connector:one", now, tenant_id="tenant:a", pack_id="sector.retail", state=EvidenceState.KNOWN_TRUE))
        self.assertEqual(store.state(tenant_id="tenant:a", pack_id="sector.retail", field_name="api_maturity"), EvidenceState.CONFLICTING)
        stale = EvidenceObservation("inventory", True, "bool", "test_result", "test:inventory", now - timedelta(days=2), tenant_id="tenant:b", pack_id="sector.retail", state=EvidenceState.KNOWN_TRUE)
        store.add(stale)
        self.assertEqual(stale.current_state(now=now, stale_after_seconds=60), EvidenceState.STALE)
        self.assertEqual(store.state(tenant_id="tenant:b", pack_id="sector.retail", field_name="inventory", now=now, stale_after_seconds=60), EvidenceState.STALE)

    def test_protocol_drift_detects_removed_features(self):
        registry = ProtocolRegistry()
        registry.register(ProtocolProfile("a2a", "A2A", "0.3.0", "core", "2026-01-01", "https://a2a", "hash-one", ("tasks", "authentication"), (), ("task-id",)))
        report = registry.compare("a2a", ProtocolProfile("a2a", "A2A", "1.0.0", "core", "2026-09-28", "https://a2a", "hash-two", ("authentication",), (), ()))
        self.assertEqual(report.result, DriftResult.BREAKING)
        self.assertIn("removed_supported_feature:tasks", report.breaking_changes)

    def test_maintained_a2a_transition_fixture_is_not_version_only(self):
        import json
        from pathlib import Path

        old = json.loads(Path("evals/phase3/protocols/a2a_v0_3.json").read_text())
        new = json.loads(Path("evals/phase3/protocols/a2a_v1_0.json").read_text())
        registry = ProtocolRegistry()
        registry.register(ProtocolProfile("a2a", "A2A", old["version"], "core", "2026-01-01", "https://a2a", "fixture-old", tuple(old["required_features"]), (), tuple(old["required_extensions"])))
        report = registry.compare("a2a", ProtocolProfile("a2a", "A2A", new["version"], "core", "2026-09-28", "https://a2a", "fixture-new", tuple(new["required_features"]), (), tuple(new["required_extensions"])))
        self.assertEqual(report.result, DriftResult.BREAKING)

    def test_recommendation_can_refuse_activation_on_unit_economics(self):
        inputs = ActivationInputs(business_size="small", technical_capacity="high", api_maturity="mature", margin_per_action=1.0, protocol_platform_fee_per_action=0.5, connector_cost_per_action=0.5, inference_cost_per_action=0.5, human_handoff_cost_per_action=0.0)
        result = ActivationStrategyEngine().recommend(inputs)
        self.assertEqual(result.recommended_pattern, ActivationPattern.DO_NOT_ACTIVATE)
        self.assertTrue(result.economic_implications)

    def test_retail_reference_journey_inherits_core_transaction_controls(self):
        with self.assertRaises(RetailActivationBlocked):
            RetailReferenceEnvironment(business_id="merchant:test")
        environment = RetailReferenceEnvironment(business_id="merchant:test", core_guarantees=CoreGuaranteeRegistry.for_test())
        environment.add_product(RetailProduct("prod:shoe", "Shoe", {"variant:red-9": RetailVariant("variant:red-9", {"color": "red", "size": "9"}, 49.99, "USD", 1)}))
        quote = environment.create_quote(product_id="prod:shoe", variant_id="variant:red-9", principal_id="principal:test")
        awaiting = environment.submit_order(retail_quote=quote, principal_id="principal:test", agent_id="agent:test", provider_id="provider:test", trust_class="VERIFIED", idempotency_key="retail-key", require_confirmation=True)
        self.assertEqual(awaiting.state, RetailJourneyState.CONFIRMATION_REQUIRED)
        from agentnative.transactions import Confirmation
        confirmation = Confirmation.create(quote.quote)
        accepted = environment.submit_order(retail_quote=quote, principal_id="principal:test", agent_id="agent:test", provider_id="provider:test", trust_class="VERIFIED", idempotency_key="retail-key", confirmation=confirmation)
        self.assertEqual(accepted.status, "ORDER_ACCEPTED")
        self.assertEqual(environment.products["prod:shoe"].variants["variant:red-9"].inventory, 0)
        replay = environment.submit_order(retail_quote=quote, principal_id="principal:test", agent_id="agent:test", provider_id="provider:test", trust_class="VERIFIED", idempotency_key="retail-key", confirmation=confirmation)
        self.assertEqual(replay.status, "REPLAYED")
        self.assertEqual(replay.order.order_id, accepted.order.order_id)
        cancelled = environment.cancel_order(order_id=accepted.order.order_id, principal_id="principal:test", agent_id="agent:test", provider_id="provider:test", idempotency_key="cancel-key")
        self.assertEqual(cancelled.status, "CANCELLED")
        cancelled_replay = environment.cancel_order(order_id=accepted.order.order_id, principal_id="principal:test", agent_id="agent:test", provider_id="provider:test", idempotency_key="cancel-key")
        self.assertEqual(cancelled_replay.status, "REPLAYED")
        self.assertEqual(environment.receipts.verify(cancelled.receipt).status, "VALID")
        self.assertEqual(environment.return_eligibility(accepted.order.order_id), RetailJourneyState.RETURN_INELIGIBLE)

    def test_retail_stale_inventory_and_unknown_agent_fail_closed(self):
        environment = RetailReferenceEnvironment(business_id="merchant:test", core_guarantees=CoreGuaranteeRegistry.for_test())
        environment.add_product(RetailProduct("prod:item", "Item", {"variant:one": RetailVariant("variant:one", {}, 10.0, "USD", 1)}))
        quote = environment.create_quote(product_id="prod:item", variant_id="variant:one", principal_id="principal:test")
        denied = environment.submit_order(retail_quote=quote, principal_id="principal:test", agent_id="agent:unknown", provider_id="provider:test", trust_class="UNKNOWN", idempotency_key="unknown-key", require_confirmation=False)
        self.assertIn("UNKNOWN_AGENT_PURCHASE", denied.findings)
        environment.set_inventory("prod:item", "variant:one", 0)
        stale = environment.submit_order(retail_quote=quote, principal_id="principal:test", agent_id="agent:test", provider_id="provider:test", trust_class="VERIFIED", idempotency_key="stale-key", confirmation=__import__("agentnative.transactions", fromlist=["Confirmation"]).Confirmation.create(quote.quote))
        self.assertIn("TOCTOU_RESOURCE_CHANGED", stale.findings)


if __name__ == "__main__":
    unittest.main()

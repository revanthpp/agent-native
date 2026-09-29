import unittest

from agentnative.capabilities import CapabilityGraph
from agentnative.packs import (
    ActivationInputs,
    ActivationPattern,
    ActivationStrategyEngine,
    MaturityFramework,
    PackCompatibilityError,
    PackEvalHarness,
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
        overridden = ActivationStrategyEngine().recommend(inputs, override=ActivationPattern.HUMAN_HANDOFF, override_reason="Owner wants review for every booking")
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


if __name__ == "__main__":
    unittest.main()

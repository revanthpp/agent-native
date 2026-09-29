import json
import tempfile
import unittest
from pathlib import Path

from agentnative.retail_product import assess_workspace, blueprint, evidence_bundle, simulate_workspace, validate_workspace


ROOT = Path(__file__).resolve().parents[2]


class RetailProductTests(unittest.TestCase):
    def test_reference_businesses_have_expected_direction(self):
        expected = {
            "direct-ready": "DIRECT",
            "platform-retailer": "PLATFORM_MEDIATED",
            "human-handoff-retailer": "HUMAN_HANDOFF",
            "unsafe-retailer": "DO_NOT_ACTIVATE",
        }
        for directory, pattern in expected.items():
            result = assess_workspace(ROOT / "examples" / "retail" / directory)
            patterns = {item["recommendation"]["recommended_pattern"] for item in result["recommendations"]}
            self.assertIn(pattern, patterns, directory)

    def test_simulation_labels_boundary_and_recovery(self):
        result = simulate_workspace(ROOT / "examples" / "retail" / "direct-ready", "lost-response")
        self.assertIn("SYNTHETIC SIMULATION", result["synthetic_boundary"])
        self.assertEqual(result["result"]["first"]["status"], "UNKNOWN_OUTCOME")
        self.assertTrue(result["input_hash"])

    def test_blueprint_and_evidence_are_reproducible_semantically(self):
        directory = ROOT / "examples" / "retail" / "platform-retailer"
        first = evidence_bundle(directory)
        second = evidence_bundle(directory)
        self.assertEqual(first["project_hash"], second["project_hash"])
        self.assertEqual(first["blueprint_hash"], second["blueprint_hash"])
        self.assertEqual(set(first["blueprint"]["roadmap_30_60_90"]), {item["journey"]["journey_id"] for item in first["assessment"]["recommendations"]})

    def test_invalid_project_rejects_secret_like_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            raw = json.loads(json.dumps({"project_id": "bad"}))
            (path / "project.yaml").write_text("project_id: bad\nsector_pack: sector.retail\napi_key: sk_test_123456789012\n", encoding="utf-8")
            with self.assertRaises(Exception):
                validate_workspace(path)


if __name__ == "__main__":
    unittest.main()

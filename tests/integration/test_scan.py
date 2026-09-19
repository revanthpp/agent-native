import json
import unittest
from pathlib import Path

from agentnative.reporting.render import render_json, render_markdown
from agentnative.scanner import scan


ROOT = Path(__file__).resolve().parents[2]


class ScanIntegrationTests(unittest.TestCase):
    def test_reference_businesses(self):
        traditional = scan(str(ROOT / "examples/traditional-business"))
        api_enabled = scan(str(ROOT / "examples/api-enabled-business"))
        agent_native = scan(str(ROOT / "examples/agent-native-business"))
        self.assertEqual(next(item.status.value for item in traditional.results if item.check.id == "AR-003"), "NOT_OBSERVED")
        self.assertEqual(next(item.status.value for item in api_enabled.results if item.check.id == "AR-003"), "PASS")
        self.assertEqual(next(item.status.value for item in agent_native.results if item.check.id == "AR-012"), "PASS")
        self.assertEqual(next(item.status.value for item in agent_native.results if item.check.id == "AR-014"), "PASS")

    def test_report_contains_summary_and_evidence(self):
        report = scan(str(ROOT / "examples/agent-native-business"))
        payload = json.loads(render_json(report))
        self.assertIn("summary", payload)
        self.assertIn("domains", payload)
        self.assertTrue(all(result["evidence"] for result in payload["results"] if result["status"] in {"PASS", "FAIL", "WARN"}))
        self.assertIn("# Agent Native Readiness Profile", render_markdown(report))

    def test_prompt_injection_is_data(self):
        report = scan(str(ROOT / "evals/adversarial/prompt-injection.html"))
        statuses = {result.check.id: result.status.value for result in report.results}
        self.assertEqual(statuses["AR-003"], "NOT_OBSERVED")
        self.assertEqual(statuses["AR-020"], "PASS")


if __name__ == "__main__":
    unittest.main()

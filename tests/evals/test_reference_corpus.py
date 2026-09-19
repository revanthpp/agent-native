import json
import unittest
from pathlib import Path

from agentnative.scanner import scan


ROOT = Path(__file__).resolve().parents[2]


class ReferenceCorpusTests(unittest.TestCase):
    def test_manifest_expectations(self):
        manifest = json.loads((ROOT / "evals/corpus/reference_businesses.json").read_text())
        for name, case in manifest.items():
            report = scan(str(ROOT / case["target"]))
            actual = {result.check.id: result.status.value for result in report.results}
            for check_id, expected in case["expected"].items():
                with self.subTest(business=name, check_id=check_id):
                    self.assertEqual(actual[check_id], expected)

    def test_static_results_are_semantically_repeatable(self):
        target = str(ROOT / "examples/agent-native-business")
        first = scan(target).to_dict()
        second = scan(target).to_dict()
        for report in (first, second):
            report.pop("scan_id", None)
            report.pop("started_at", None)
            report.pop("completed_at", None)
            for artifact in report["artifacts"]:
                artifact.pop("acquisition_timestamp", None)
            for result in report["results"]:
                for evidence in result["evidence"]:
                    evidence.pop("acquisition_timestamp", None)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

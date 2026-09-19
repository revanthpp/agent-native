from __future__ import annotations

import json
import unittest
from pathlib import Path

from agentnative.checks.catalog import CHECKS
from agentnative.scanner import scan


ROOT = Path(__file__).resolve().parents[2]


class CheckMatrixTests(unittest.TestCase):
    def test_every_check_has_positive_negative_and_missing_evidence_fixtures(self) -> None:
        matrix = json.loads((ROOT / "evals/corpus/check_matrix.json").read_text())
        entries = {entry["check_id"]: entry for entry in matrix["entries"]}
        self.assertEqual(set(entries), {check.id for check in CHECKS})
        for entry in entries.values():
            for key in ("positive_fixture", "negative_fixture", "missing_evidence_fixture"):
                self.assertTrue((ROOT / entry[key]).exists(), f"missing fixture: {entry[key]}")
            self.assertTrue(entry["expected_signal"])

    def test_matrix_fixtures_produce_observable_results_without_check_errors(self) -> None:
        matrix = json.loads((ROOT / "evals/corpus/check_matrix.json").read_text())
        targets = {fixture for entry in matrix["entries"] for key in ("positive_fixture", "negative_fixture", "missing_evidence_fixture") for fixture in [entry[key]]}
        for fixture in targets:
            with self.subTest(fixture=fixture):
                report = scan(str(ROOT / fixture))
                self.assertTrue(report.results)
                self.assertFalse([result for result in report.results if result.status.value == "ERROR"])


if __name__ == "__main__":
    unittest.main()

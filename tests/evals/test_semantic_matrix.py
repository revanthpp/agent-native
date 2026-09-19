from __future__ import annotations

import json
import unittest
from pathlib import Path

from agentnative.scanner import scan


ROOT = Path(__file__).resolve().parents[2]


class SemanticMatrixTests(unittest.TestCase):
    def test_expected_status_is_asserted_for_each_case(self) -> None:
        matrix = json.loads((ROOT / "evals/corpus/semantic_matrix.json").read_text())
        for case in matrix["cases"]:
            with self.subTest(case=case):
                report = scan(str(ROOT / case["fixture"]))
                result = next(item for item in report.results if item.check.id == case["check_id"])
                self.assertEqual(result.status.value, case["expected_status"])


if __name__ == "__main__":
    unittest.main()

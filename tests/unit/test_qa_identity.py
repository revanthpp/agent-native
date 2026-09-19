from __future__ import annotations

import unittest
from pathlib import Path

from scripts.qa_identity import verify_repository


ROOT = Path(__file__).resolve().parents[2]


class QAIdentityTests(unittest.TestCase):
    def test_expected_workspace_is_confirmed(self) -> None:
        self.assertTrue(verify_repository(ROOT))

    def test_missing_marker_is_rejected(self) -> None:
        self.assertFalse(verify_repository(ROOT / "missing-workspace"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class Gate2ProofRemediationTests(unittest.TestCase):
    def test_first_party_tamper_matrix_rejects_all_cases(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_phase3b_evidence_tamper_matrix.py")],
            cwd=ROOT,
            env=dict(os.environ, PYTHONPATH=str(ROOT / "src")),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["counts"], {"total": 30, "rejected": 30, "accepted": 0})
        self.assertEqual(result["known_good_online"], "EVIDENCE_VALID")
        self.assertEqual(result["known_good_offline"], "OFFLINE_PARTIAL_VERIFICATION")


if __name__ == "__main__":
    unittest.main()

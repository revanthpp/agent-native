from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentnative.evidence.validator import EvidenceIntegrityError, validate_evidence
from agentnative.reporting.render import render_json, render_markdown, render_terminal
from agentnative.scanner import scan


ROOT = Path(__file__).resolve().parents[2]


class ReportIntegrityTests(unittest.TestCase):
    def test_public_projection_excludes_artifact_payload_and_headers(self) -> None:
        report = scan(str(ROOT / "evals/adversarial/secret-bearing.html"))
        payload = json.loads(render_json(report))
        self.assertTrue(payload["artifacts"])
        for artifact in payload["artifacts"]:
            self.assertNotIn("content", artifact)
            self.assertNotIn("headers", artifact)
            self.assertIn("content_hash", artifact)
        self.assertEqual(payload["execution_status"], "completed")

    def test_blocked_target_credentials_are_not_echoed(self) -> None:
        report = scan("https://user:super-secret@example.com/path?api_key=top-secret")
        payload = render_json(report)
        self.assertNotIn("super-secret", payload)
        self.assertNotIn("top-secret", payload)
        self.assertIn("https://example.com/path", payload)

    def test_tampered_evidence_is_rejected_before_rendering(self) -> None:
        report = scan(str(ROOT / "examples/agent-native-business"))
        result = next(item for item in report.results if item.evidence)
        result.evidence[0].content_hash = "0" * 64
        with self.assertRaises(EvidenceIntegrityError):
            validate_evidence(report)
        with self.assertRaises(EvidenceIntegrityError):
            render_json(report)

    def test_parse_and_acquisition_failures_are_observable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text('<a href="/openapi.json">API</a>', encoding="utf-8")
            (root / "openapi.json").write_text("{not-json", encoding="utf-8")
            report = scan(root)
            artifact = next(item for item in report.artifacts if item.uri.endswith("openapi.json"))
            self.assertEqual(artifact.parse_status.value, "PARSE_ERROR")
            self.assertTrue(artifact.error)
            rendered = render_markdown(report)
            self.assertIn("Artifact parse failure", rendered)

    def test_terminal_output_removes_control_sequences(self) -> None:
        report = scan(str(ROOT / "examples/traditional-business"))
        report.limitations.append("\x1b[2Jerase\x1b[0m")
        output = render_terminal(report)
        self.assertNotIn("\x1b", output)
        self.assertIn("erase", output)


if __name__ == "__main__":
    unittest.main()

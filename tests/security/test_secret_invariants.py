from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentnative.checks.catalog import CHECK_BY_ID
from agentnative.models import Artifact, CheckResult, Evidence, Limitation, ResultStatus, ScanReport, Target, utc_now
from agentnative.reporting.output import UnsafeReportError, validate_output
from agentnative.reporting.render import render_json, render_markdown, render_terminal
from agentnative.scanner import scan
from agentnative.security.canonicalize import SecretCanonicalizer
from agentnative.security.sanitize import Sanitizer
from agentnative.security.secrets import REDACTION_MARKER, SecretDetector


ROOT = Path(__file__).resolve().parents[2]


class SecretInvariantTests(unittest.TestCase):
    credential_values = {
        "bearer": "FAKE_BEARER_TOKEN_1234567890",
        "token": "FAKE_TOKEN_1234567890",
        "secret": "FAKE_SECRET_1234567890",
        "session_id": "FAKE_SESSION_ID_1234567890",
        "sessionid": "FAKE_SESSIONID_1234567890",
        "api_key": "FAKE_API_KEY_1234567890",
        "client_secret": "FAKE_CLIENT_SECRET_1234567890",
        "password": "FAKE_PASSWORD_1234567890",
        "cookie": "FAKE_COOKIE_1234567890",
    }

    def test_canonical_detector_and_sanitizer_cover_required_forms(self) -> None:
        detector = SecretDetector()
        sanitizer = Sanitizer(detector)
        forms = [
            "Authorization: Bearer FAKE_BEARER_TOKEN_1234567890",
            "token=FAKE_TOKEN_1234567890",
            "secret: FAKE_SECRET_1234567890",
            "session_id = FAKE_SESSION_ID_1234567890",
            "sessionid=FAKE_SESSIONID_1234567890",
            '{"api_key": "FAKE_API_KEY_1234567890"}',
            "client_secret: 'FAKE_CLIENT_SECRET_1234567890'",
            "password=FAKE_PASSWORD_1234567890",
            "Cookie: session=FAKE_COOKIE_1234567890",
        ]
        for value in forms:
            with self.subTest(value=value):
                self.assertTrue(detector.detect_text(value))
                safe, changed = sanitizer.text(value)
                self.assertTrue(changed)
                self.assertNotIn(value.split("=")[-1].strip(" '\""), safe)
                self.assertIn(REDACTION_MARKER, safe)

    def test_bounded_percent_canonicalization(self) -> None:
        canonicalizer = SecretCanonicalizer(max_decode_passes=2)
        self.assertEqual(canonicalizer.variants("token=FAKE"), ("token=FAKE",))
        self.assertEqual(canonicalizer.variants("token%3DFAKE")[-1], "token=FAKE")
        self.assertEqual(canonicalizer.variants("token%3dFAKE")[-1], "token=FAKE")
        self.assertEqual(canonicalizer.variants("token%253DFAKE")[-1], "token=FAKE")
        self.assertEqual(canonicalizer.variants("token%25253DFAKE")[-1], "token%3DFAKE")
        self.assertFalse(SecretDetector().detect_text("token%25253DFAKE"))
        self.assertEqual(canonicalizer.variants("token=FAKE")[-1], canonicalizer.variants(canonicalizer.variants("token=FAKE")[-1])[-1])

    def test_uri_components_are_canonicalized_before_detection(self) -> None:
        sanitizer = Sanitizer()
        uris = [
            "https://example.com/missing/token%3DFAKE_PATH_TOKEN_1234567890",
            "https://example.com/#token%3DFAKE_FRAGMENT_TOKEN_1234567890",
            "https://example.com/?token%3DFAKE_QUERY_TOKEN_1234567890",
            "https://example.com/?x=token%3DFAKE_NESTED_TOKEN_1234567890",
            "https://user:FAKE_PASSWORD@example.com/",
        ]
        for uri in uris:
            with self.subTest(uri=uri):
                safe = sanitizer.uri(uri)
                self.assertNotIn("FAKE_", safe)
                self.assertFalse(SecretDetector().detect_text(safe))

    def test_canonicalization_terminates_on_percent_heavy_input(self) -> None:
        value = "%25" * 10000 + "token%253DFAKE"
        variants = SecretCanonicalizer().variants(value)
        self.assertLessEqual(len(variants), 3)
        self.assertLessEqual(max(len(item) for item in variants), len(value))

    def test_safe_percent_encoding_does_not_create_findings(self) -> None:
        detector = SecretDetector()
        for value in ("hello%20world", "page%3Ddocumentation", "token%20budget", "session%20timeout", "password%20policy"):
            with self.subTest(value=value):
                self.assertFalse(detector.detect_text(value))

    def test_safe_keyword_language_does_not_fail_ar020(self) -> None:
        report = scan(str(ROOT / "evals/adversarial/credentials/safe-token-language.html"))
        result = next(item for item in report.results if item.check.id == "AR-020")
        self.assertEqual(result.status, ResultStatus.PASS)
        self.assertFalse(SecretDetector().detect({"token": "budgeting", "secret": "management", "password": "policy"}))
        self.assertFalse(SecretDetector().detect_text("Bearer token authentication is documented here"))

    def test_deterministic_generated_credential_variants(self) -> None:
        detector = SecretDetector()
        sanitizer = Sanitizer(detector)
        for key in ("token", "TOKEN", "session_id", "client-secret", "api_key"):
            for separator in ("=", ":"):
                value = f"FAKE_{key.upper().replace('-', '_')}_VARIANT_1234567890"
                for wrapper in ("", '"'):
                    sample = f"{wrapper}{key}{wrapper} {separator} {wrapper}{value}{wrapper}"
                    with self.subTest(sample=sample):
                        self.assertTrue(detector.detect_text(sample))
                        safe, _ = sanitizer.text(sample)
                        self.assertNotIn(value, safe)
                        self.assertIn(REDACTION_MARKER, safe)

    def test_ar020_semantic_credential_matrix(self) -> None:
        fixture_dir = ROOT / "evals/adversarial/credentials"
        for fixture in sorted(fixture_dir.glob("*.html")):
            expected = ResultStatus.PASS if fixture.name.startswith("safe-") else ResultStatus.FAIL
            with self.subTest(fixture=fixture.name):
                result = next(item for item in scan(str(fixture)).results if item.check.id == "AR-020")
                self.assertEqual(result.status, expected)

    def test_no_detected_secret_reaches_any_renderer(self) -> None:
        for fixture, raw_value in self.credential_values.items():
            path = ROOT / "evals/adversarial/credentials" / f"{fixture.replace('_', '-')}.html"
            if not path.exists():
                path = ROOT / "evals/adversarial/credentials" / ("sessionid.html" if fixture == "sessionid" else f"{fixture}.html")
            report = scan(str(path))
            for render in (render_json, render_markdown, render_terminal):
                with self.subTest(fixture=fixture, renderer=render.__name__):
                    output = render(report)
                    self.assertNotIn(raw_value, output)
                    self.assertIn("redacted", output.lower())

    def test_encoded_credential_fixtures_fail_and_are_safe_in_all_formats(self) -> None:
        fixtures = {
            "encoded-body.html": "FAKE_BODY_ENCODED_TOKEN_1234567890",
            "double-encoded.html": "FAKE_DOUBLE_ENCODED_TOKEN_1234567890",
            "encoded-bearer.html": "FAKE_BEARER_1234567890",
        }
        for name, raw_value in fixtures.items():
            report = scan(str(ROOT / "evals/adversarial/credentials" / name))
            result = next(item for item in report.results if item.check.id == "AR-020")
            self.assertEqual(result.status, ResultStatus.FAIL)
            for render in (render_json, render_markdown, render_terminal):
                with self.subTest(fixture=name, renderer=render.__name__):
                    output = render(report)
                    self.assertNotIn(raw_value, output)
                    self.assertNotIn(raw_value.replace("=", "%3D"), output)

    def test_nested_structures_and_uri_queries_use_same_detector(self) -> None:
        detector = SecretDetector()
        sanitizer = Sanitizer(detector)
        value = {"headers": ["Authorization: Bearer FAKE_NESTED_TOKEN_1234567890"], "query": {"token": "FAKE_QUERY_TOKEN_1234567890"}}
        self.assertTrue(detector.detect(value))
        safe = sanitizer.value(value)
        serialized = json.dumps(safe)
        self.assertFalse(detector.detect(serialized))
        self.assertEqual(
            sanitizer.uri("https://example.com/openapi.json?token=FAKE_QUERY_TOKEN_1234567890&view=full"),
            "https://example.com/openapi.json?token=[REDACTED]&view=full",
        )

    def test_structured_limitations_and_evidence_source_uris_are_safe(self) -> None:
        content = "safe"
        artifact = Artifact(
            uri="https://example.com/openapi.json?x=token%3DFAKE_SOURCE_TOKEN_1234567890",
            artifact_type="http",
            content=content,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
            acquisition_timestamp=utc_now(),
        )
        result = CheckResult(
            CHECK_BY_ID["AR-003"],
            ResultStatus.PASS,
            "source observed",
            "keep it documented",
            1.0,
            [Evidence("ev-1", artifact.uri, "http", utc_now(), artifact.content_hash, artifact.artifact_id, "AR-003", artifact.uri, {}, "source", 1.0)],
        )
        report = ScanReport("scan-1", Target("x", "x", "network"), utc_now(), utc_now(), "1.0.0", "1.0.0", [result], [artifact], [Limitation("DISCOVERY_FETCH_FAILED", "https://example.com/missing/token%253DFAKE_LIMITATION_TOKEN_1234567890", "token%3DFAKE_LIMITATION_REASON_1234567890")])
        for render in (render_json, render_markdown, render_terminal):
            output = render(report)
            self.assertNotIn("FAKE_SOURCE_TOKEN_1234567890", output)
            self.assertNotIn("FAKE_LIMITATION_TOKEN_1234567890", output)
            self.assertNotIn("FAKE_LIMITATION_REASON_1234567890", output)
            self.assertIn("[REDACTED]", output)

    def test_final_output_firewall_fails_closed_without_echoing_secret(self) -> None:
        report = scan(str(ROOT / "examples/traditional-business"))
        unsafe = report.public_projection()
        unsafe.target = Target("https://example.com/?token=FAKE_FIREWALL_TOKEN_1234567890", "https://example.com/?token=FAKE_FIREWALL_TOKEN_1234567890", "network")
        with patch("agentnative.reporting.render.SafeReportBuilder.build", return_value=unsafe):
            with self.assertRaises(UnsafeReportError) as raised:
                render_json(report)
        self.assertNotIn("FAKE_FIREWALL_TOKEN_1234567890", str(raised.exception))

    def test_direct_output_validator_is_fail_closed(self) -> None:
        with self.assertRaises(UnsafeReportError):
            validate_output("source=https://example.com/?token=FAKE_DIRECT_TOKEN_1234567890")


if __name__ == "__main__":
    unittest.main()

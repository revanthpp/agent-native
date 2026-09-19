import json
import unittest
from pathlib import Path

from agentnative.models import ResultStatus
from agentnative.parsers.html import parse_html
from agentnative.parsers.openapi import parse_openapi
from agentnative.security.policy import NetworkPolicy, UnsafeTargetError, validate_network_url
from agentnative.security.redaction import redact


ROOT = Path(__file__).resolve().parents[2]


class CoreTests(unittest.TestCase):
    def test_html_parser_does_not_execute_script(self):
        parsed = parse_html('<script>window.pwned = true</script><a href="/openapi.json">API</a>')
        self.assertEqual(parsed["links"], ["/openapi.json"])

    def test_openapi_parser_normalizes_operations(self):
        raw = json.loads((ROOT / "examples/agent-native-business/openapi.json").read_text())
        doc = parse_openapi(json.dumps(raw), "file:///openapi.json")
        self.assertEqual(len(doc.operations), 4)
        self.assertEqual(doc.operations[-1].operation_id, "cancelReservation")

    def test_redaction(self):
        value, changed = redact("Authorization: Bearer abc123 secret=topsecret")
        self.assertTrue(changed)
        self.assertNotIn("topsecret", value)
        self.assertIn("[REDACTED]", value)

    def test_network_policy_rejects_unsafe_targets(self):
        policy = NetworkPolicy()
        for url in ("file:///etc/passwd", "ftp://example.com", "https://user:pass@example.com", "https://127.0.0.1"):
            with self.subTest(url=url):
                with self.assertRaises(UnsafeTargetError):
                    validate_network_url(url, policy)

    def test_http_requires_explicit_fixture_policy(self):
        with self.assertRaises(UnsafeTargetError):
            validate_network_url("http://127.0.0.1:8000", NetworkPolicy())


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from agentnative.scanner import scan
from agentnative.security.policy import NetworkPolicy, UnsafeTargetError, validate_network_url


ROOT = Path(__file__).resolve().parents[2]


class SecurityTests(unittest.TestCase):
    def test_private_ipv4_and_ipv6_are_blocked(self):
        for url in ("https://10.0.0.1", "https://192.168.1.1", "https://[::1]", "https://169.254.169.254"):
            with self.subTest(url=url):
                with self.assertRaises(UnsafeTargetError):
                    validate_network_url(url, NetworkPolicy())

    def test_secret_fixture_is_failed_and_redacted(self):
        report = scan(str(ROOT / "evals/adversarial/secret-bearing.html"))
        result = next(item for item in report.results if item.check.id == "AR-020")
        self.assertEqual(result.status.value, "FAIL")
        self.assertTrue(all("sk_example_not_for_use" not in evidence.relevant_fragment for evidence in result.evidence))


if __name__ == "__main__":
    unittest.main()

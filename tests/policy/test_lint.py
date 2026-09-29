import unittest
from datetime import datetime, timedelta, timezone

from agentnative.policy import Decision, PolicyLinter, PolicyRule


class PolicyLintTests(unittest.TestCase):
    def test_missing_default(self):
        self.assertTrue(any(item.startswith("POL-LINT-001") for item in PolicyLinter().lint([PolicyRule("allow", capability="read", decision=Decision.ALLOW, owner="x")])))

    def test_unowned_expired_and_future(self):
        now = datetime.now(timezone.utc)
        findings = PolicyLinter().lint([PolicyRule("expired", expires_at=now-timedelta(seconds=1)), PolicyRule("future", effective_at=now+timedelta(seconds=1))], now=now)
        self.assertTrue(any("POL-LINT-002" in item for item in findings)); self.assertTrue(any("POL-LINT-003" in item for item in findings)); self.assertTrue(any("POL-LINT-004" in item for item in findings))

    def test_wildcard_sensitive_action_and_confirmation(self):
        findings = PolicyLinter().lint([PolicyRule("allow-purchase", capability="purchase", decision=Decision.ALLOW, owner="security")])
        self.assertTrue(any("POL-LINT-005" in item for item in findings)); self.assertTrue(any("POL-LINT-008" in item for item in findings))

    def test_contradiction_duplicate_and_unreachable(self):
        rules = [PolicyRule("broad", capability="purchase", decision=Decision.ALLOW, owner="security", priority=10), PolicyRule("shadowed", capability="purchase", decision=Decision.ALLOW, owner="security", priority=1), PolicyRule("deny", capability="purchase", decision=Decision.DENY, owner="security", priority=1)]
        findings = PolicyLinter().lint(rules)
        self.assertTrue(any("POL-LINT-006" in item for item in findings)); self.assertTrue(any("POL-LINT-007" in item for item in findings)); self.assertTrue(any("POL-LINT-009" in item for item in findings))

    def test_environment_inconsistency(self):
        findings = PolicyLinter().lint([PolicyRule("production-wildcard", environment="PRODUCTION_ACTIVE", owner="security")])
        self.assertTrue(any("POL-LINT-010" in item for item in findings))


if __name__ == "__main__": unittest.main()

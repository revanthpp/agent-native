from __future__ import annotations

from datetime import datetime, timezone

from agentnative.policy.models import Decision, PolicyRule


class PolicyLinter:
    def lint(self, rules: list[PolicyRule], *, now: datetime | None = None) -> list[str]:
        current = now or datetime.now(timezone.utc); findings: list[str] = []
        defaults = [rule for rule in rules if rule.capability is None and rule.trust_class is None and rule.provider_id is None and rule.agent_id is None]
        if not any(rule.decision == Decision.DENY for rule in defaults): findings.append("POL-LINT-001:missing_default")
        seen: dict[tuple[object, ...], PolicyRule] = {}
        for rule in rules:
            if rule.owner is None: findings.append(f"POL-LINT-002:unowned_rule:{rule.policy_id}")
            if rule.expires_at and current >= rule.expires_at: findings.append(f"POL-LINT-003:expired_rule:{rule.policy_id}")
            if rule.effective_at and current < rule.effective_at: findings.append(f"POL-LINT-004:future_rule:{rule.policy_id}")
            if rule.decision == Decision.ALLOW and rule.trust_class is None and rule.capability is not None: findings.append(f"POL-LINT-005:wildcard_privilege:{rule.policy_id}")
            key = (rule.trust_class, rule.provider_id, rule.agent_id, rule.capability, rule.resource, rule.environment, rule.geography, rule.data_class, rule.priority)
            if key in seen and seen[key].decision != rule.decision: findings.append(f"POL-LINT-006:contradictory_rules:{seen[key].policy_id},{rule.policy_id}")
            if key in seen: findings.append(f"POL-LINT-009:duplicate_ambiguity:{rule.policy_id}")
            seen[key] = rule
            if rule.priority < max((other.priority for other in rules if other is not rule and PolicyLinter._shadows(other, rule)), default=-1): findings.append(f"POL-LINT-007:unreachable_rule:{rule.policy_id}")
            if rule.decision == Decision.ALLOW and rule.capability and any(word in rule.capability.lower() for word in ("purchase", "transfer", "delete", "refund")) and not rule.required_confirmation: findings.append(f"POL-LINT-008:high_risk_without_confirmation:{rule.policy_id}")
            if rule.environment == "PRODUCTION_ACTIVE" and rule.capability is None: findings.append(f"POL-LINT-010:environment_inconsistency:{rule.policy_id}")
        return sorted(set(findings))

    @staticmethod
    def _shadows(broad: PolicyRule, narrow: PolicyRule) -> bool:
        selectors = ("trust_class", "provider_id", "agent_id", "capability", "resource", "environment", "geography", "data_class")
        return broad.decision == narrow.decision and broad.priority > narrow.priority and all(getattr(broad, key) is None or getattr(broad, key) == getattr(narrow, key) for key in selectors)

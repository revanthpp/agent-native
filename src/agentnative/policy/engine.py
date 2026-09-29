from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from agentnative.capabilities.models import Capability
from agentnative.protocols.models import ActionClass
from agentnative.identity.models import AgentIdentity
from agentnative.delegation.models import DelegationGrant
from agentnative.policy.models import Decision, PolicyDecision, PolicyRule


@dataclass(frozen=True)
class PolicyControls:
    """Production policy gates with narrow seams for mutation testing."""

    explicit_deny_precedence: bool = True
    default_deny: bool = True
    policy_version: bool = True


class PolicyEngine:
    def __init__(self, rules: list[PolicyRule], version: str = "1") -> None: self.rules, self.version = list(rules), version

    @staticmethod
    def matches(rule: PolicyRule, identity: AgentIdentity, capability: Capability, context: dict[str, Any]) -> bool:
        return all(expected is None or expected == actual for expected, actual in ((rule.trust_class, identity.trust_class.value), (rule.provider_id, identity.provider_id), (rule.agent_id, identity.agent_id), (rule.capability, capability.capability_id), (rule.resource, context.get("resource")), (rule.environment, context.get("environment")), (rule.geography, context.get("geography")), (rule.data_class, context.get("data_class"))))

    def evaluate(self, identity: AgentIdentity, grant: DelegationGrant | None, capability: Capability, context: dict[str, Any], *, controls: PolicyControls | None = None) -> PolicyDecision:
        controls = controls or PolicyControls()
        if controls.policy_version and context.get("policy_version") is not None and context.get("policy_version") != self.version:
            return PolicyDecision(Decision.DENY, None, self.version, "policy version mismatch", required_next_action="reload_policy")
        if capability.action_class not in {ActionClass.READ, ActionClass.RECOMMEND, ActionClass.PREVIEW} and grant is None: return PolicyDecision(Decision.DENY, None, self.version, "state-changing action requires delegation", required_next_action="provide_valid_delegation")
        now = datetime.now(timezone.utc); matches=[]; defaults=[]
        for rule in self.rules:
            if rule.expires_at and now >= rule.expires_at or rule.effective_at and now < rule.effective_at: continue
            if self.matches(rule, identity, capability, context):
                (defaults if rule.capability is None and rule.trust_class is None and rule.provider_id is None and rule.agent_id is None else matches).append(rule)
        matches.sort(key=lambda item: item.priority, reverse=True)
        selected = (next((rule for rule in matches if rule.decision == Decision.DENY), None) if controls.explicit_deny_precedence else None) or (matches[0] if matches else (defaults[0] if defaults else None))
        if selected: return PolicyDecision(selected.decision, selected.policy_id, selected.version, selected.reason, required_next_action="confirm_with_human" if selected.decision == Decision.REQUIRE_HUMAN else None)
        return PolicyDecision(Decision.DENY if controls.default_deny else Decision.ALLOW, None, self.version, "no matching policy rule", required_next_action="request_policy_authorization" if controls.default_deny else None)

from __future__ import annotations

from typing import Any

from dataclasses import dataclass

from agentnative.policy.engine import PolicyControls, PolicyEngine
from agentnative.policy.models import Decision, PolicyDecision
from agentnative.capabilities.models import Capability
from agentnative.identity.signatures import IntegrityResult
from agentnative.delegation.models import DelegationControls, DelegationGrant
from agentnative.identity.models import AgentIdentity


@dataclass(frozen=True)
class AuthorizationControls:
    owner_verification: bool = True
    signature_verification: bool = True
    replay_protection: bool = True
    delegation: DelegationControls = DelegationControls()
    policy: PolicyControls = PolicyControls()


def authorize_state_change(*, owner_verified: bool, identity: AgentIdentity | None, integrity: IntegrityResult, grant: DelegationGrant | None, capability: Capability, engine: PolicyEngine, context: dict[str, Any], controls: AuthorizationControls | None = None) -> PolicyDecision:
    controls = controls or AuthorizationControls()
    if controls.owner_verification and not owner_verified: return PolicyDecision(Decision.DENY, None, engine.version, "owner verification required", required_next_action="verify_owner")
    if controls.signature_verification and (identity is None or not integrity.valid): return PolicyDecision(Decision.DENY, None, engine.version, "verified identity and request integrity required", required_next_action="authenticate_agent")
    if controls.replay_protection and getattr(integrity, "reason", "") == "replay_detected": return PolicyDecision(Decision.DENY, None, engine.version, "replay detected", required_next_action="reject_replay")
    if grant is None: return PolicyDecision(Decision.DENY, None, engine.version, "delegation required", required_next_action="provide_valid_delegation")
    if identity is None: return PolicyDecision(Decision.DENY, None, engine.version, "verified identity and request integrity required", required_next_action="authenticate_agent")
    allowed, reason = grant.authorize(principal=context.get("principal"), agent_id=identity.agent_id, provider_id=identity.provider_id, capability_id=capability.capability_id, resource=context.get("resource"), audience=context.get("audience"), value=context.get("value"), currency=context.get("currency"), geography=context.get("geography"), controls=controls.delegation)
    return engine.evaluate(identity, grant, capability, context, controls=controls.policy) if allowed else PolicyDecision(Decision.DENY, None, engine.version, reason)

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class DelegationControls:
    """Production authorization gates; mutation tests may disable one at a time."""

    expiry: bool = True
    revocation: bool = True
    principal_binding: bool = True
    agent_binding: bool = True
    provider_binding: bool = True
    capability_binding: bool = True
    audience_binding: bool = True
    resource_binding: bool = True
    value_limit: bool = True
    geography_binding: bool = True


@dataclass(frozen=True)
class DelegationGrant:
    grant_id: str; principal_reference: str; agent_id: str; provider_id: str; capability_ids: frozenset[str]; resource_boundary: str | None = None; scopes: frozenset[str] = frozenset(); value_limit: float | None = None; currency: str | None = None; geography: str | None = None; valid_from: datetime | None = None; expires_at: datetime | None = None; confirmation_policy: str | None = None; audience: str | None = None; revoked: bool = False
    def authorize(self, *, principal, agent_id, provider_id, capability_id, resource=None, audience=None, value=None, currency=None, geography=None, now=None, controls: DelegationControls | None = None):
        controls = controls or DelegationControls()
        current=now or datetime.now(timezone.utc)
        if controls.revocation and self.revoked: return False, "grant_revoked"
        if controls.expiry and self.valid_from and current < self.valid_from: return False, "grant_not_yet_valid"
        if controls.expiry and self.expires_at and current >= self.expires_at: return False, "grant_expired"
        bindings = (
            (controls.principal_binding, self.principal_reference, principal, "principal_mismatch"),
            (controls.agent_binding, self.agent_id, agent_id, "agent_mismatch"),
            (controls.provider_binding, self.provider_id, provider_id, "provider_mismatch"),
        )
        for enabled, expected, actual, reason in bindings:
            if enabled and expected != actual: return False, reason
        if controls.capability_binding and capability_id not in self.capability_ids: return False, "capability_not_granted"
        if controls.audience_binding and self.audience and audience != self.audience: return False, "audience_mismatch"
        if controls.resource_binding and self.resource_boundary and resource != self.resource_boundary: return False, "resource_mismatch"
        if controls.value_limit and self.value_limit is not None and (value is None or value > self.value_limit): return False, "value_limit_exceeded"
        if controls.value_limit and self.value_limit is not None and self.currency and (not isinstance(currency, str) or currency.strip().upper() != self.currency.strip().upper()): return False, "currency_mismatch"
        if controls.geography_binding and self.geography and geography != self.geography: return False, "geography_restricted"
        return True, "authorized"
    def scope_findings(self, required_scopes):
        findings=[]; missing=sorted(set(required_scopes)-set(self.scopes))
        if missing: findings.append("insufficient_scope:" + ",".join(missing))
        if set(self.scopes)-set(required_scopes): findings.append("overbroad_scope")
        return tuple(findings)

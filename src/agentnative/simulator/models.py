from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from agentnative.delegation.models import DelegationGrant
from agentnative.identity.models import AgentIdentity, TrustClass
from agentnative.identity.signatures import IntegrityResult
from agentnative.ownership.models import Environment, OwnershipVerification, VerificationStatus
from agentnative.capabilities.models import Capability
from agentnative.protocols.models import ActionClass, SideEffect
from agentnative.transactions.core import Confirmation, FailureInjection, Quote, public_amount, stable_hash, transaction_fingerprint
from agentnative.receipts.core import Receipt
from agentnative.simulator.state import ScenarioState


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return value if isinstance(value, datetime) else None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class SimulationStatus(StrEnum):
    DRY_RUN = "DRY_RUN"
    WOULD_ALLOW = "WOULD_ALLOW"
    WOULD_DENY = "WOULD_DENY"
    WOULD_REQUIRE_HUMAN = "WOULD_REQUIRE_HUMAN"
    EXECUTED = "EXECUTED"
    DENIED = "DENIED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    COMPENSATED = "COMPENSATED"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"


@dataclass
class Scenario:
    scenario_id: str
    name: str
    business_id: str
    capability: Capability
    target_environment: Environment = Environment.SANDBOX
    principal: str = ""
    description: str = ""
    input: dict[str, Any] = field(default_factory=dict)
    agent_identity: AgentIdentity | None = None
    integrity: IntegrityResult | None = None
    delegation: DelegationGrant | None = None
    ownership: OwnershipVerification | None = None
    policy_engine: Any | None = None
    confirmation_behavior: str = "NONE"
    value: Any = None
    currency: Any = "USD"
    resource_reference: str = "resource:synthetic"
    audience: str | None = None
    timeout_seconds: int = 30
    max_retries: int = 2
    failure_injections: tuple[FailureInjection, ...] = ()
    expected_risk: str = "UNKNOWN"
    expected_policy_outcome: str = "UNKNOWN"
    expected_outcome: str = "UNKNOWN"
    compensation_required: bool = False
    version: str = "1"
    idempotency_key: str | None = None

    @property
    def requires_confirmation(self) -> bool:
        return self.confirmation_behavior.upper() in {"REQUIRED", "REQUIRE_HUMAN", "HUMAN"}

    @property
    def request_hash(self) -> str:
        return self.transaction_fingerprint()

    def transaction_fingerprint(self, *, quote_id: str | None = None, confirmation_id: str | None = None) -> str:
        identity = self.agent_identity
        return transaction_fingerprint(
            business_id=self.business_id,
            environment=self.target_environment,
            principal_id=self.principal,
            agent_id=identity.agent_id if identity else None,
            provider_id=identity.provider_id if identity else None,
            capability_id=self.capability.capability_id,
            resource_reference=self.resource_reference,
            value=self.value,
            currency=self.currency,
            input_data=self.input,
            quote_id=quote_id,
            confirmation_id=confirmation_id,
        )

    def safe_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "business_id": self.business_id,
            "target_environment": self.target_environment.value,
            "principal": self.principal,
            "capability_id": self.capability.capability_id,
            "action_class": self.capability.action_class.value,
            "resource_reference": self.resource_reference,
            "value": public_amount(self.value),
            "currency": self.currency,
            "input_hash": stable_hash(self.input),
            "confirmation_behavior": self.confirmation_behavior,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Scenario":
        if not isinstance(raw, dict):
            raise ValueError("scenario must be an object")
        capability_raw = raw.get("capability") if isinstance(raw.get("capability"), dict) else {}
        capability_id = str(capability_raw.get("capability_id") or raw.get("capability_id") or "capability:unknown")
        action = ActionClass(str(capability_raw.get("action_class") or raw.get("action_class") or "UNKNOWN").upper())
        capability = Capability(capability_id, str(capability_raw.get("business_id") or raw.get("business_id") or "business:unknown"), str(capability_raw.get("name") or capability_id), str(capability_raw.get("description") or ""), action_class=action, side_effect=SideEffect(str(capability_raw.get("side_effect") or "UNKNOWN").upper()))
        identity_raw = raw.get("agent_identity")
        identity = None
        if isinstance(identity_raw, dict):
            identity = AgentIdentity(str(identity_raw.get("agent_id") or ""), str(identity_raw.get("provider_id") or ""), str(identity_raw.get("display_name") or "agent"), TrustClass(str(identity_raw.get("trust_class") or "UNKNOWN").upper()), str(identity_raw.get("identity_method") or "scenario"), identity_raw.get("key_id"))
        integrity_raw = raw.get("integrity")
        integrity = IntegrityResult(bool(integrity_raw.get("valid")), str(integrity_raw.get("reason") or "scenario"), integrity_raw.get("key_id"), integrity_raw.get("agent_id"), integrity_raw.get("nonce")) if isinstance(integrity_raw, dict) else None
        grant_raw = raw.get("delegation")
        grant = None
        if isinstance(grant_raw, dict):
            grant = DelegationGrant(str(grant_raw.get("grant_id") or "grant:scenario"), str(grant_raw.get("principal_reference") or raw.get("principal") or ""), str(grant_raw.get("agent_id") or (identity.agent_id if identity else "")), str(grant_raw.get("provider_id") or (identity.provider_id if identity else "")), frozenset(str(item) for item in grant_raw.get("capability_ids", [capability_id])), resource_boundary=grant_raw.get("resource_boundary"), scopes=frozenset(str(item) for item in grant_raw.get("scopes", [])), value_limit=grant_raw.get("value_limit"), currency=grant_raw.get("currency"), expires_at=_parse_time(grant_raw.get("expires_at")), audience=grant_raw.get("audience"), revoked=bool(grant_raw.get("revoked", False)))
        ownership_raw = raw.get("ownership") or raw.get("ownership_verification")
        ownership = None
        if isinstance(ownership_raw, dict):
            ownership = OwnershipVerification(str(ownership_raw.get("verification_id") or "verification:scenario"), str(ownership_raw.get("business_id") or raw.get("business_id") or ""), str(ownership_raw.get("target") or raw.get("target") or "scenario"), str(ownership_raw.get("method") or "scenario"), str(ownership_raw.get("challenge_hash") or "scenario"), _parse_time(ownership_raw.get("verified_at")) or datetime.now(timezone.utc), _parse_time(ownership_raw.get("expires_at")) or datetime.now(timezone.utc), Environment(str(ownership_raw.get("environment") or raw.get("target_environment") or "SANDBOX").upper()), VerificationStatus(str(ownership_raw.get("status") or "INVALID").upper()), "scenario")
        policy_engine = None
        policy_raw = raw.get("policy")
        if isinstance(policy_raw, dict):
            policy_rules_raw = policy_raw.get("rules", [])
            policy_version = str(policy_raw.get("version") or "1")
        else:
            policy_rules_raw = policy_raw if isinstance(policy_raw, list) else []
            policy_version = "1"
        if isinstance(policy_rules_raw, list):
            from agentnative.policy import Decision, PolicyEngine, PolicyRule

            rules = []
            for item in policy_rules_raw:
                if not isinstance(item, dict) or not item.get("policy_id"):
                    continue
                values = {key: value for key, value in item.items() if key in {field for field in PolicyRule.__dataclass_fields__}}
                values["decision"] = Decision(str(values.get("decision", "DENY")).upper())
                rules.append(PolicyRule(**values))
            policy_engine = PolicyEngine(rules, version=policy_version)
        injections = tuple(FailureInjection.from_dict(item) for item in raw.get("failure_injections", []) if isinstance(item, dict))
        value = raw.get("value")
        ceiling = raw.get("value_ceiling")
        if value is None and ceiling is not None:
            value = ceiling
        currency = raw["currency"] if "currency" in raw else "USD"
        retry_policy = raw.get("retry_policy") if isinstance(raw.get("retry_policy"), dict) else {}
        return cls(str(raw.get("scenario_id") or "scenario:unnamed"), str(raw.get("name") or "Unnamed scenario"), str(raw.get("business_id") or capability.business_id), capability, Environment(str(raw.get("target_environment") or "SANDBOX").upper()), str(raw.get("principal") or ""), str(raw.get("description") or ""), raw.get("input") if isinstance(raw.get("input"), dict) else {}, identity, integrity, grant, ownership, policy_engine, str(raw.get("confirmation_behavior") or "NONE"), value, currency, str(raw.get("resource_reference") or "resource:synthetic"), raw.get("audience"), int(raw.get("timeout_seconds") or 30), int(retry_policy.get("max_retries", raw.get("max_retries", 2))), injections, str(raw.get("expected_risk") or "UNKNOWN"), str(raw.get("expected_policy_outcome") or "UNKNOWN"), str(raw.get("expected_outcome") or "UNKNOWN"), bool(raw.get("compensation_required", False)), str(raw.get("version") or "1"), raw.get("idempotency_key"))


@dataclass
class SimulationResult:
    run_id: str
    scenario_id: str
    status: SimulationStatus
    state: ScenarioState
    decision: str
    message: str
    transitions: list[dict[str, Any]] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    quote: Quote | None = None
    confirmation: Confirmation | None = None
    receipt: Receipt | None = None
    trace: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    idempotency_key: str | None = None
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        def quote_dict(value: Quote | None) -> dict[str, Any] | None:
            if value is None:
                return None
            return {"quote_id": value.quote_id, "capability_id": value.capability_id, "resource_reference": value.resource_reference, "value": public_amount(value.value), "currency": value.currency, "created_at": value.created_at.isoformat(), "expires_at": value.expires_at.isoformat(), "version": value.version, "principal_reference": value.principal_reference, "business_id": value.business_id, "environment": value.environment.value, "evidence_refs": list(value.evidence_refs)}

        return {"run_id": self.run_id, "scenario_id": self.scenario_id, "status": self.status.value, "state": self.state.value, "decision": self.decision, "message": self.message, "transitions": self.transitions, "findings": list(self.findings), "limitations": list(self.limitations), "quote": quote_dict(self.quote), "confirmation_id": self.confirmation.confirmation_id if self.confirmation else None, "receipt": self.receipt.to_dict() if self.receipt else None, "trace": self.trace, "attempts": self.attempts, "idempotency_key": self.idempotency_key, "dry_run": self.dry_run}


__all__ = ["Scenario", "SimulationResult", "SimulationStatus"]

from __future__ import annotations

import json
import math
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from agentnative.capabilities.models import Capability
from agentnative.delegation import DelegationGrant
from agentnative.identity import AgentIdentity, IntegrityResult, TrustClass
from agentnative.observability import TraceContext, TraceRecorder
from agentnative.ownership import Environment, OwnershipVerification, VerificationStatus
from agentnative.policy import Decision, PolicyEngine, PolicyRule
from agentnative.protocols.models import ActionClass, SideEffect
from agentnative.receipts import ReceiptEngine
from agentnative.simulator import Scenario, Simulator, SyntheticExecutionAdapter
from agentnative.transactions import Confirmation, ExecutionResult, FailureInjection, FailurePoint, Quote


def make_scenario(
    *,
    action: ActionClass = ActionClass.CREATE,
    environment: Environment = Environment.SANDBOX,
    confirmation: str = "NONE",
    value: Any = 10.0,
    currency: str | None = "USD",
    key: str | None = None,
    resource: str = "resource:synthetic",
    injections: tuple[FailureInjection, ...] = (),
    compensation: bool = False,
    policy: PolicyEngine | None = None,
    grant: DelegationGrant | None = None,
) -> Scenario:
    now = datetime.now(timezone.utc)
    capability = Capability("cap:stress", "business:stress", "stress action", action_class=action, side_effect=SideEffect.REVERSIBLE)
    identity = AgentIdentity("agent:stress", "provider:stress", "Stress Agent", TrustClass.CRYPTOGRAPHICALLY_VERIFIED)
    ownership = OwnershipVerification(
        "verification:stress",
        "business:stress",
        "sandbox.stress",
        "fixture",
        "challenge",
        now - timedelta(seconds=1),
        now + timedelta(hours=1),
        environment,
        VerificationStatus.VERIFIED,
        "fixture",
    )
    grant = grant or DelegationGrant(
        "grant:stress",
        "principal:stress",
        identity.agent_id,
        identity.provider_id,
        frozenset({capability.capability_id}),
        resource_boundary=resource,
        value_limit=100,
        currency="USD",
    )
    policy = policy or PolicyEngine([PolicyRule("allow-stress", trust_class=identity.trust_class.value, capability=capability.capability_id, environment=environment.value, decision=Decision.ALLOW, owner="audit")])
    return Scenario(
        "scenario:stress",
        "Phase 2C stress scenario",
        "business:stress",
        capability,
        environment,
        "principal:stress",
        agent_identity=identity,
        integrity=IntegrityResult(True, "verified", "key:stress", identity.agent_id, "nonce:stress"),
        delegation=grant,
        ownership=ownership,
        policy_engine=policy,
        confirmation_behavior=confirmation,
        value=value,
        currency=currency,
        resource_reference=resource,
        failure_injections=injections,
        compensation_required=compensation,
        idempotency_key=key,
    )


def record(name: str, passed: bool, **evidence: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), **evidence}


def test_risk_value_edges() -> list[dict[str, Any]]:
    simulator = Simulator()
    cases: list[tuple[str, Any, str | None, str]] = [
        ("below_limit", 99.99, "USD", "EXECUTED"),
        ("at_limit", 100.0, "USD", "EXECUTED"),
        ("above_limit", 100.01, "USD", "DENIED"),
        ("missing_value", None, "USD", "DENIED"),
        ("nan_value", math.nan, "USD", "DENIED"),
        ("negative_value", -1.0, "USD", "DENIED"),
        ("wrong_currency", 10.0, "EUR", "DENIED"),
        ("missing_currency", 10.0, None, "DENIED"),
    ]
    output = []
    for label, value, currency, expected in cases:
        result = simulator.run(make_scenario(value=value, currency=currency, key=f"risk-{label}-{time.time_ns()}"))
        output.append(record(f"risk_{label}", result.status.value == expected, expected=expected, actual=result.status.value, findings=result.findings, value_repr=repr(value), currency=currency))
    return output


class MutatingPreviewAdapter(SyntheticExecutionAdapter):
    def prepare(self, scenario: Any) -> None:
        self.resource.version += 1
        self.resource.changed = True

    def preview(self, scenario: Any):
        self.resource.version += 1
        self.resource.changed = True
        return super().preview(scenario)


def test_dry_run_side_effect_trap() -> dict[str, Any]:
    adapter = MutatingPreviewAdapter(value=10)
    before = adapter.snapshot()
    result = Simulator().run(make_scenario(key=f"dry-{time.time_ns()}"), adapter, dry_run=True)
    after = adapter.snapshot()
    return record("dry_run_preview_prepare_side_effect_trap", before == after, expected_snapshot=before, actual_snapshot=after, status=result.status.value, dry_run=result.dry_run)


class RaceAdapter(SyntheticExecutionAdapter):
    def __init__(self, parties: int) -> None:
        super().__init__(value=10)
        self.barrier = threading.Barrier(parties)
        self.commit_count = 0
        self.lock = threading.Lock()

    def execute(self, scenario: Any, quote: Quote, idempotency_key: str) -> ExecutionResult:
        self.barrier.wait(timeout=10)
        with self.lock:
            self.commit_count += 1
            self.resource.version += 1
            self.resource.changed = True
            version = str(self.resource.version)
        return ExecutionResult("SUCCESS", f"race-result-{version}", True, "REVERSIBLE", version, False, "non-idempotent audit adapter")


def test_concurrent_idempotency() -> dict[str, Any]:
    parties = 8
    simulator = Simulator()
    adapter = RaceAdapter(parties)
    statuses: list[str] = []

    def run_one() -> str:
        return simulator.run(make_scenario(key="shared-concurrent-key"), adapter).status.value

    with ThreadPoolExecutor(max_workers=parties) as pool:
        futures = [pool.submit(run_one) for _ in range(parties)]
        for future in as_completed(futures):
            statuses.append(future.result())

    passed = adapter.commit_count == 1 and adapter.resource.version == 2 and statuses.count("EXECUTED") == parties
    return record("concurrent_same_key_single_side_effect", passed, statuses=sorted(statuses), commit_count=adapter.commit_count, resource_version=adapter.resource.version)


def test_confirmation_controls() -> list[dict[str, Any]]:
    simulator = Simulator()
    scenario = make_scenario(confirmation="REQUIRED", key=f"confirm-{time.time_ns()}")
    awaiting = simulator.run(scenario)
    confirmation = Confirmation.create(awaiting.quote)
    wrong_principal = replace(confirmation, principal_reference="principal:other")
    wrong = simulator.run(make_scenario(confirmation="REQUIRED", key=f"confirm-wrong-{time.time_ns()}"), confirmation=wrong_principal, quote=awaiting.quote)
    executed = simulator.run(make_scenario(confirmation="REQUIRED", key=f"confirm-ok-{time.time_ns()}"), confirmation=confirmation, quote=awaiting.quote)
    replay = simulator.run(make_scenario(confirmation="REQUIRED", key=f"confirm-replay-{time.time_ns()}"), confirmation=confirmation, quote=awaiting.quote)
    expired = simulator.run(make_scenario(confirmation="REQUIRED", key=f"confirm-expired-{time.time_ns()}"), confirmation=Confirmation.create(awaiting.quote, ttl=timedelta(seconds=-1)), quote=awaiting.quote)
    return [
        record("confirmation_required_blocks_commit", awaiting.status.value == "AWAITING_CONFIRMATION", actual=awaiting.status.value),
        record("confirmation_wrong_principal_rejected", wrong.status.value == "FAILED", actual=wrong.status.value, findings=wrong.findings),
        record("confirmation_valid_executes", executed.status.value == "EXECUTED", actual=executed.status.value),
        record("confirmation_replay_rejected", replay.status.value == "FAILED", actual=replay.status.value, findings=replay.findings),
        record("confirmation_expired_rejected", expired.status.value == "FAILED", actual=expired.status.value, findings=expired.findings),
    ]


def test_quote_policy_partial_receipt_trace() -> list[dict[str, Any]]:
    stale = Simulator().run(make_scenario(injections=(FailureInjection(FailurePoint.AFTER_PREVIEW, "STALE_RESOURCE"),), key=f"stale-{time.time_ns()}"))
    partial = Simulator().run(make_scenario(injections=(FailureInjection(FailurePoint.DURING_RESPONSE, "PARTIAL_SUCCESS"),), key=f"partial-{time.time_ns()}"))
    compensated = Simulator().run(make_scenario(injections=(FailureInjection(FailurePoint.DURING_RESPONSE, "PARTIAL_SUCCESS"),), compensation=True, key=f"comp-{time.time_ns()}"))

    policy = PolicyEngine([PolicyRule("allow-stress", trust_class="CRYPTOGRAPHICALLY_VERIFIED", capability="cap:stress", environment="SANDBOX", decision=Decision.ALLOW, owner="audit")])

    class PolicyChangingAdapter(SyntheticExecutionAdapter):
        def preview(self, scenario: Any):
            preview = super().preview(scenario)
            policy.version = "2"
            return preview

    policy_change = Simulator().run(make_scenario(policy=policy, key=f"policy-{time.time_ns()}"), PolicyChangingAdapter())

    secret = "Bearer PHASE2C_SECRET_1234567890"
    recorder = TraceRecorder(TraceContext.new("correlation:secret"))
    recorder.emit("secret_probe", {"authorization": secret, "nested": {"api_key": "sk-proj-PHASE2CSECRET1234567890"}})
    trace = recorder.export()

    receipt_engine = ReceiptEngine()
    receipt = receipt_engine.create(
        business_id="business:stress",
        environment="SANDBOX",
        agent_id="agent:stress",
        provider_id="provider:stress",
        principal_reference=f"token={secret}",
        capability_id="cap:stress",
        policy_id="policy",
        policy_version="1",
        decision="ALLOW",
        delegation_reference="grant:stress",
        confirmation_reference=None,
        quote_reference="quote",
        request_hash="a" * 64,
        result="EXECUTED",
        side_effect="REVERSIBLE",
        resource_reference="resource:synthetic",
        value=10,
        currency="USD",
        correlation_id="correlation",
        trace_id="trace",
        evidence_refs=("policy_decided",),
    )
    modified = {**receipt.to_dict(), "value": 11}
    return [
        record("stale_quote_detected", stale.status.value == "FAILED" and "TOCTOU_RESOURCE_CHANGED" in stale.findings, actual=stale.status.value, findings=stale.findings),
        record("partial_outcome_not_success", partial.status.value == "PARTIAL", actual=partial.status.value, findings=partial.findings),
        record("compensation_success_reported", compensated.status.value == "COMPENSATED", actual=compensated.status.value, findings=compensated.findings),
        record("policy_change_between_preview_commit_denied", policy_change.status.value == "DENIED", actual=policy_change.status.value, findings=policy_change.findings),
        record("trace_redacts_secrets", secret not in repr(trace) and "PHASE2CSECRET" not in repr(trace), trace_repr=repr(trace)),
        record("receipt_redacts_and_verifies", secret not in repr(receipt.to_dict()) and receipt_engine.verify(receipt).status == "VALID", receipt=receipt.to_dict()),
        record("receipt_tamper_detected", receipt_engine.verify(modified).status == "INVALID", verification=receipt_engine.verify(modified).status),
    ]


def main() -> int:
    checks = []
    checks.extend(test_risk_value_edges())
    checks.append(test_dry_run_side_effect_trap())
    checks.append(test_concurrent_idempotency())
    checks.extend(test_confirmation_controls())
    checks.extend(test_quote_policy_partial_receipt_trace())

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total": len(checks),
        "passed": sum(1 for item in checks if item["passed"]),
        "failed": [item for item in checks if not item["passed"]],
        "checks": checks,
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if not payload["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

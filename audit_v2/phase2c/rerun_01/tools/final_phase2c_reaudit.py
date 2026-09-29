from __future__ import annotations

import json
import math
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from agentnative.capabilities.models import Capability
from agentnative.delegation import DelegationGrant
from agentnative.identity import AgentIdentity, IntegrityResult, TrustClass
from agentnative.ownership import Environment, OwnershipVerification, VerificationStatus
from agentnative.policy import Decision, PolicyEngine, PolicyRule
from agentnative.protocols.models import ActionClass, SideEffect
from agentnative.receipts import ReceiptEngine
from agentnative.simulator import Scenario, Simulator, SimulatorControls, SyntheticExecutionAdapter
from agentnative.transactions import Confirmation, ExecutionResult, FailureClass, FailureInjection, FailurePoint, PreviewResult, Quote, TransactionSafetyError, VerificationResult, default_risk_ceiling


def case(name: str, passed: bool, **evidence: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), **evidence}


def make_scenario(
    *,
    scenario_id: str = "scenario:audit",
    action: ActionClass = ActionClass.CREATE,
    capability_id: str = "cap:audit",
    business_id: str = "business:audit",
    environment: Environment = Environment.SANDBOX,
    principal: str = "principal:audit",
    agent_id: str = "agent:audit",
    provider_id: str = "provider:audit",
    confirmation: str = "NONE",
    value: Any = Decimal("10.00"),
    currency: Any = "USD",
    key: str | None = None,
    resource: str = "resource:audit",
    input_data: dict[str, Any] | None = None,
    policy_decision: Decision = Decision.ALLOW,
    policy: PolicyEngine | None = None,
    grant_revoked: bool = False,
    max_retries: int = 2,
    timeout_seconds: int = 2,
    injections: tuple[FailureInjection, ...] = (),
) -> Scenario:
    now = datetime.now(timezone.utc)
    capability = Capability(capability_id, business_id, "audit capability", action_class=action, side_effect=SideEffect.REVERSIBLE)
    identity = AgentIdentity(agent_id, provider_id, "Audit Agent", TrustClass.CRYPTOGRAPHICALLY_VERIFIED)
    ownership = OwnershipVerification(
        f"verification:{scenario_id}",
        business_id,
        "audit.synthetic",
        "fixture",
        "challenge",
        now - timedelta(seconds=1),
        now + timedelta(hours=1),
        environment,
        VerificationStatus.VERIFIED,
        "fixture",
    )
    grant = DelegationGrant(
        f"grant:{scenario_id}",
        principal,
        agent_id,
        provider_id,
        frozenset({capability_id}),
        resource_boundary=resource,
        value_limit=1000,
        currency="USD",
        revoked=grant_revoked,
    )
    policy = policy or PolicyEngine([PolicyRule(f"policy:{scenario_id}", trust_class=identity.trust_class.value, capability=capability_id, environment=environment.value, decision=policy_decision, owner="audit")])
    return Scenario(
        scenario_id,
        "Phase 2C final re-audit scenario",
        business_id,
        capability,
        environment,
        principal,
        agent_identity=identity,
        integrity=IntegrityResult(True, "verified", "key:audit", agent_id, "nonce:audit"),
        delegation=grant,
        ownership=ownership,
        policy_engine=policy,
        confirmation_behavior=confirmation,
        value=value,
        currency=currency,
        resource_reference=resource,
        input=input_data or {},
        idempotency_key=key,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
        failure_injections=injections,
    )


class NonIdempotentCountingAdapter(SyntheticExecutionAdapter):
    def __init__(self, *, value: Any = Decimal("10.00"), currency: Any = "USD", resource_reference: str = "resource:audit", sleep_seconds: float = 0.0, jitter: bool = False) -> None:
        super().__init__(resource_reference=resource_reference, value=value, currency=currency)
        self.sleep_seconds = sleep_seconds
        self.jitter = jitter
        self.execution_count = 0
        self.side_effect_count = 0
        self.lock = threading.Lock()

    def execute(self, scenario: Any, quote: Quote, idempotency_key: str) -> ExecutionResult:
        if self.jitter:
            time.sleep(random.random() / 1000)
        elif self.sleep_seconds:
            time.sleep(self.sleep_seconds)
        with self.lock:
            self.execution_count += 1
            self.side_effect_count += 1
            self.resource.version += 1
            self.resource.changed = True
            version = str(self.resource.version)
        return ExecutionResult("SUCCESS", f"result-{version}", True, "REVERSIBLE", version)


class BlockingAdapter(NonIdempotentCountingAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.release = threading.Event()

    def execute(self, scenario: Any, quote: Quote, idempotency_key: str) -> ExecutionResult:
        with self.lock:
            self.execution_count += 1
        self.entered.set()
        self.release.wait(timeout=5)
        with self.lock:
            self.side_effect_count += 1
            self.resource.version += 1
            self.resource.changed = True
            version = str(self.resource.version)
        return ExecutionResult("SUCCESS", f"blocked-result-{version}", True, "REVERSIBLE", version)


class InstrumentedDryRunAdapter(SyntheticExecutionAdapter):
    def __init__(self, *, mutate_active: bool = False, mutate_plan: bool = False, external_store: dict[str, int] | None = None) -> None:
        super().__init__(value=Decimal("10.00"), currency="USD")
        self.counts = {"constructor": 1, "build_plan": 0, "prepare": 0, "preview": 0, "execute": 0, "verify": 0, "compensate": 0}
        self.mutate_active = mutate_active
        self.mutate_plan = mutate_plan
        self.external_store = external_store if external_store is not None else {"business_state": 0}

    def _mutate(self) -> None:
        self.external_store["business_state"] += 1
        self.resource.version += 1
        self.resource.changed = True

    def build_plan(self, scenario: Any) -> PreviewResult:
        self.counts["build_plan"] += 1
        if self.mutate_plan:
            self._mutate()
        return super().build_plan(scenario)

    def prepare(self, scenario: Any) -> None:
        self.counts["prepare"] += 1
        if self.mutate_active:
            self._mutate()
        return super().prepare(scenario)

    def preview(self, scenario: Any) -> PreviewResult:
        self.counts["preview"] += 1
        if self.mutate_active:
            self._mutate()
        return super().preview(scenario)

    def execute(self, scenario: Any, quote: Quote, idempotency_key: str) -> ExecutionResult:
        self.counts["execute"] += 1
        if self.mutate_active:
            self._mutate()
        return super().execute(scenario, quote, idempotency_key)

    def verify(self, scenario: Any, execution: ExecutionResult) -> VerificationResult:
        self.counts["verify"] += 1
        return super().verify(scenario, execution)

    def compensate(self, scenario: Any, execution: ExecutionResult) -> ExecutionResult:
        self.counts["compensate"] += 1
        return super().compensate(scenario, execution)


class ExternalOnlyPlanMutationAdapter(InstrumentedDryRunAdapter):
    def build_plan(self, scenario: Any) -> PreviewResult:
        self.counts["build_plan"] += 1
        self.external_store["business_state"] += 1
        return SyntheticExecutionAdapter.build_plan(self, scenario)


def money_retest() -> list[dict[str, Any]]:
    expectations = [
        ("zero", Decimal("0"), "USD", "EXECUTED"),
        ("cent", Decimal("0.01"), "USD", "EXECUTED"),
        ("below", Decimal("99.99"), "USD", "EXECUTED"),
        ("at", Decimal("100.00"), "USD", "EXECUTED"),
        ("above", Decimal("100.01"), "USD", "DENIED"),
        ("negative_cent", Decimal("-0.01"), "USD", "DENIED"),
        ("negative_one", Decimal("-1"), "USD", "DENIED"),
        ("nan_float", float("nan"), "USD", "DENIED"),
        ("inf_float", float("inf"), "USD", "DENIED"),
        ("neg_inf_float", float("-inf"), "USD", "DENIED"),
        ("none", None, "USD", "DENIED"),
        ("true_bool", True, "USD", "DENIED"),
        ("false_bool", False, "USD", "DENIED"),
        ("string_100", "100", "USD", "DENIED"),
        ("string_100_decimal", "100.00", "USD", "DENIED"),
        ("string_nan", "NaN", "USD", "DENIED"),
        ("huge_decimal", Decimal("1000000000000000.01"), "USD", "DENIED"),
        ("missing_currency", Decimal("10"), None, "DENIED"),
        ("wrong_currency", Decimal("10"), "EUR", "DENIED"),
        ("lowercase_currency", Decimal("10"), "usd", "EXECUTED"),
        ("whitespace_currency", Decimal("10"), " usd ", "EXECUTED"),
        ("unknown_currency", Decimal("10"), "BTC", "DENIED"),
    ]
    output = []
    for label, value, currency, expected in expectations:
        adapter = NonIdempotentCountingAdapter(value=value, currency=currency)
        result = Simulator().run(make_scenario(scenario_id=f"money:{label}", value=value, currency=currency, key=f"money:{label}:{time.time_ns()}"), adapter)
        no_execution_on_invalid = expected == "EXECUTED" or adapter.execution_count == 0
        output.append(case(f"money_{label}", result.status.value == expected and no_execution_on_invalid, expected=expected, actual=result.status.value, findings=result.findings, execution_count=adapter.execution_count, value=repr(value), currency=repr(currency)))
    ceiling = default_risk_ceiling(Environment.SANDBOX)
    direct = {
        "bool_rejected": ceiling.allows(ActionClass.CREATE, True, "USD") == (False, "RISK_VALUE_INVALID"),
        "numeric_string_rejected": ceiling.allows(ActionClass.CREATE, "100", "USD") == (False, "RISK_VALUE_INVALID"),
        "lowercase_normalized": ceiling.allows(ActionClass.CREATE, Decimal("10"), "usd")[0],
        "no_fx": ceiling.allows(ActionClass.CREATE, Decimal("10"), "EUR") == (False, "RISK_CURRENCY_MISMATCH"),
    }
    output.append(case("money_representation_review", all(direct.values()), details=direct))
    return output


def concurrency_harness_a(workers: int, rounds: int) -> dict[str, Any]:
    failures = []
    for round_index in range(rounds):
        simulator = Simulator()
        adapter = NonIdempotentCountingAdapter(sleep_seconds=0.005)
        barrier = threading.Barrier(workers)

        def run_one() -> str:
            barrier.wait(timeout=10)
            return simulator.run(make_scenario(scenario_id=f"conc-a:{round_index}", key=f"conc-a:{round_index}"), adapter).status.value

        with ThreadPoolExecutor(max_workers=workers) as pool:
            statuses = list(pool.map(lambda _: run_one(), range(workers)))
        if adapter.side_effect_count != 1 or any(status != "EXECUTED" for status in statuses):
            failures.append({"round": round_index, "execution_count": adapter.execution_count, "side_effect_count": adapter.side_effect_count, "statuses": statuses})
    return case(f"concurrency_a_barrier_before_transaction_{workers}w_{rounds}r", not failures, failures=failures[:5], rounds=rounds, workers=workers)


def concurrency_harness_b(workers: int = 8) -> dict[str, Any]:
    simulator = Simulator()
    adapter = BlockingAdapter()
    start = threading.Barrier(workers)
    statuses: list[str] = []

    def run_one() -> str:
        start.wait(timeout=10)
        return simulator.run(make_scenario(scenario_id="conc-b", key="conc-b-key", timeout_seconds=3), adapter).status.value

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_one) for _ in range(workers)]
        adapter.entered.wait(timeout=2)
        time.sleep(0.05)
        entered_before_release = adapter.execution_count
        adapter.release.set()
        for future in as_completed(futures):
            statuses.append(future.result())
    passed = entered_before_release == 1 and adapter.execution_count == 1 and adapter.side_effect_count == 1 and statuses.count("EXECUTED") == workers
    return case("concurrency_b_slow_side_effect_pending_waiters", passed, entered_before_release=entered_before_release, execution_count=adapter.execution_count, side_effect_count=adapter.side_effect_count, statuses=sorted(statuses))


def concurrency_harness_c(workers: int = 8, rounds: int = 100) -> dict[str, Any]:
    random.seed(20260928)
    duplicate_rounds = []
    errors = []
    for round_index in range(rounds):
        simulator = Simulator()
        adapter = NonIdempotentCountingAdapter(jitter=True)
        start = threading.Barrier(workers)

        def run_one(worker: int) -> str:
            time.sleep(random.random() / 1000)
            start.wait(timeout=10)
            return simulator.run(make_scenario(scenario_id=f"conc-c:{round_index}", key=f"conc-c:{round_index}"), adapter).status.value

        with ThreadPoolExecutor(max_workers=workers) as pool:
            statuses = list(pool.map(run_one, range(workers)))
        if adapter.side_effect_count != 1:
            duplicate_rounds.append({"round": round_index, "side_effect_count": adapter.side_effect_count, "execution_count": adapter.execution_count})
        if any(status != "EXECUTED" for status in statuses):
            errors.append({"round": round_index, "statuses": statuses})
    return case("concurrency_c_scheduler_pressure_8w_100r", not duplicate_rounds, duplicate_side_effect_rounds=len(duplicate_rounds), duplicate_examples=duplicate_rounds[:5], non_executed_rounds=len(errors), non_executed_examples=errors[:5])


def changed_request_conflicts() -> list[dict[str, Any]]:
    dimensions = [
        ("amount", {"value": Decimal("20.00")}),
        ("currency", {"currency": "EUR"}),
        ("resource", {"resource": "resource:other"}),
        ("principal", {"principal": "principal:other"}),
        ("agent", {"agent_id": "agent:other"}),
        ("capability", {"capability_id": "cap:other"}),
        ("environment", {"environment": Environment.STAGING}),
        ("payload", {"input_data": {"changed": True}}),
    ]
    results = []
    for dimension, overrides in dimensions:
        simulator = Simulator()
        adapter = NonIdempotentCountingAdapter()
        key = f"changed:{dimension}"
        first = simulator.run(make_scenario(scenario_id=f"changed:{dimension}:a", key=key), adapter)
        second = simulator.run(make_scenario(scenario_id=f"changed:{dimension}:b", key=key, **overrides), adapter)
        conflict = (second.status.value == "FAILED" and "IDEMPOTENCY_KEY_REUSE" in second.findings) or second.status.value in {"DENIED", "FAILED"}
        no_second_effect = adapter.side_effect_count == 1
        results.append(case(f"same_key_changed_{dimension}_conflicts", conflict and no_second_effect, first=first.status.value, second=second.status.value, findings=second.findings, side_effect_count=adapter.side_effect_count, first_hash=make_scenario(scenario_id=f"changed:{dimension}:a", key=key).request_hash, second_hash=make_scenario(scenario_id=f"changed:{dimension}:b", key=key, **overrides).request_hash))
    return results


def request_hash_audit() -> dict[str, Any]:
    base = make_scenario()
    mutations = {
        "amount": make_scenario(value=Decimal("11.00")).request_hash,
        "currency": make_scenario(currency="EUR").request_hash,
        "resource": make_scenario(resource="resource:other").request_hash,
        "principal": make_scenario(principal="principal:other").request_hash,
        "agent": make_scenario(agent_id="agent:other").request_hash,
        "capability": make_scenario(capability_id="cap:other").request_hash,
        "environment": make_scenario(environment=Environment.STAGING).request_hash,
        "payload": make_scenario(input_data={"changed": True}).request_hash,
    }
    covered = {name: value != base.request_hash for name, value in mutations.items()}
    required = ["amount", "currency", "resource", "principal", "agent", "capability", "environment", "payload"]
    return case("request_hash_material_dimensions", all(covered[item] for item in required), base_hash=base.request_hash, covered=covered)


class RetryableBeforeEffectAdapter(NonIdempotentCountingAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.fail_once = True

    def execute(self, scenario: Any, quote: Quote, idempotency_key: str) -> ExecutionResult:
        if self.fail_once:
            self.fail_once = False
            raise TransactionSafetyError("AUDIT_BEFORE_SIDE_EFFECT", "retryable before side effect", FailureClass.RETRYABLE, state_changed=False)
        return super().execute(scenario, quote, idempotency_key)


class UnknownAfterEffectAdapter(NonIdempotentCountingAdapter):
    def execute(self, scenario: Any, quote: Quote, idempotency_key: str) -> ExecutionResult:
        with self.lock:
            self.execution_count += 1
            self.side_effect_count += 1
            self.resource.version += 1
            self.resource.changed = True
        raise TransactionSafetyError("AUDIT_AFTER_SIDE_EFFECT", "response/persistence lost after side effect", FailureClass.UNKNOWN, state_changed=True)


def failure_recovery_tests() -> list[dict[str, Any]]:
    before_adapter = RetryableBeforeEffectAdapter()
    simulator = Simulator()
    first = simulator.run(make_scenario(scenario_id="before-fail", key="before-fail-key", max_retries=0), before_adapter)
    second = simulator.run(make_scenario(scenario_id="before-fail", key="before-fail-key", max_retries=0), before_adapter)

    after_adapter = UnknownAfterEffectAdapter()
    simulator2 = Simulator()
    after_first = simulator2.run(make_scenario(scenario_id="after-fail", key="after-fail-key", max_retries=0), after_adapter)
    after_second = simulator2.run(make_scenario(scenario_id="after-fail", key="after-fail-key", max_retries=0), after_adapter)

    hang_adapter = BlockingAdapter()
    simulator3 = Simulator()
    owner_status: list[str] = []

    def owner() -> None:
        owner_status.append(simulator3.run(make_scenario(scenario_id="hang", key="hang-key", timeout_seconds=1), hang_adapter).status.value)

    t = threading.Thread(target=owner)
    t.start()
    hang_adapter.entered.wait(timeout=2)
    waiter = simulator3.run(make_scenario(scenario_id="hang", key="hang-key", timeout_seconds=1), hang_adapter)
    hang_adapter.release.set()
    t.join(timeout=3)
    return [
        case("owner_failure_before_side_effect_retryable_recovers", first.status.value == "FAILED" and second.status.value == "EXECUTED" and before_adapter.side_effect_count == 1, first=first.status.value, first_findings=first.findings, second=second.status.value, side_effect_count=before_adapter.side_effect_count),
        case("owner_failure_after_side_effect_unknown_blocks_retry", after_first.status.value == "PARTIAL" and after_second.status.value == "FAILED" and "IDEMPOTENCY_UNKNOWN_OUTCOME" in after_second.findings and after_adapter.side_effect_count == 1, first=after_first.status.value, first_findings=after_first.findings, second=after_second.status.value, second_findings=after_second.findings, side_effect_count=after_adapter.side_effect_count),
        case("idempotency_waiter_timeout_is_bounded", waiter.status.value == "FAILED" and "IDEMPOTENCY_IN_PROGRESS" in waiter.findings and owner_status == ["EXECUTED"], waiter=waiter.status.value, waiter_findings=waiter.findings, owner_status=owner_status, execution_count=hang_adapter.execution_count, side_effect_count=hang_adapter.side_effect_count),
    ]


def lost_response_test() -> dict[str, Any]:
    adapter = SyntheticExecutionAdapter(failure_injections=(FailureInjection(FailurePoint.AFTER_COMMIT_BEFORE_RESPONSE, "RESPONSE_LOST"),), value=Decimal("10.00"), currency="USD")
    result = Simulator().run(make_scenario(scenario_id="lost-response", key="lost-response-key"), adapter)
    second = Simulator().run(make_scenario(scenario_id="lost-response-fresh-simulator", key="lost-response-key"), adapter)
    return case("lost_response_after_success_one_effect_per_simulator", result.status.value == "EXECUTED" and adapter.resource.version == 2, first=result.status.value, attempts=result.attempts, adapter_version=adapter.resource.version, second_fresh_simulator=second.status.value)


def dry_run_tests() -> list[dict[str, Any]]:
    store = {"business_state": 0}
    adapter = InstrumentedDryRunAdapter(mutate_active=True, external_store=store)
    before = adapter.snapshot()
    result = Simulator().run(make_scenario(scenario_id="dry-active", key="dry-active-key"), adapter, dry_run=True)
    after = adapter.snapshot()

    plan_store = {"business_state": 0}
    mutating_plan = InstrumentedDryRunAdapter(mutate_plan=True, external_store=plan_store)
    plan_result = Simulator().run(make_scenario(scenario_id="dry-plan", key="dry-plan-key"), mutating_plan, dry_run=True)
    external_only_store = {"business_state": 0}
    external_only = ExternalOnlyPlanMutationAdapter(external_store=external_only_store)
    external_only_result = Simulator().run(make_scenario(scenario_id="dry-external-only", key="dry-external-only-key"), external_only, dry_run=True)

    required = Simulator().run(make_scenario(scenario_id="dry-human", confirmation="REQUIRED", key="dry-human-key"), InstrumentedDryRunAdapter(), dry_run=True)
    denied = Simulator().run(make_scenario(scenario_id="dry-deny", value=Decimal("101.00"), key="dry-deny-key"), InstrumentedDryRunAdapter(), dry_run=True)
    return [
        case("dry_run_invokes_build_plan_only", result.status.value == "WOULD_ALLOW" and before == after and store["business_state"] == 0 and adapter.counts == {"constructor": 1, "build_plan": 1, "prepare": 0, "preview": 0, "execute": 0, "verify": 0, "compensate": 0}, status=result.status.value, counts=adapter.counts, state_delta=store["business_state"], before=before, after=after, quote_terms=result.quote.terms if result.quote else None),
        case("dry_run_mutating_build_plan_fails_closed_after_detectable_snapshot_change", plan_result.status.value == "WOULD_DENY" and "DRY_RUN_SIDE_EFFECT" in plan_result.findings and plan_store["business_state"] == 1, status=plan_result.status.value, findings=plan_result.findings, counts=mutating_plan.counts, external_state_delta=plan_store["business_state"]),
        case("dry_run_external_only_plan_mutation_not_generically_detected", external_only_result.status.value == "WOULD_ALLOW" and external_only_store["business_state"] == 1, status=external_only_result.status.value, findings=external_only_result.findings, counts=external_only.counts, external_state_delta=external_only_store["business_state"], classification="trust_boundary_observation"),
        case("dry_run_requires_human_honestly", required.status.value == "WOULD_REQUIRE_HUMAN", status=required.status.value, side_effect=required.receipt.side_effect if required.receipt else None),
        case("dry_run_denies_invalid_risk_before_execution", denied.status.value == "WOULD_DENY", status=denied.status.value, findings=denied.findings),
    ]


def cross_control_tests() -> list[dict[str, Any]]:
    confirmation_required = Simulator().run(make_scenario(scenario_id="risk-confirm", confirmation="REQUIRED", value=Decimal("99.00"), key="risk-confirm-key"))

    class PriceChangingAdapter(SyntheticExecutionAdapter):
        def __init__(self) -> None:
            super().__init__(value=Decimal("99.00"), currency="USD")

        def preview(self, scenario: Any) -> PreviewResult:
            preview = super().preview(scenario)
            self.resource.value = Decimal("101.00")
            self.resource.version += 1
            return preview

    toctou = Simulator().run(make_scenario(scenario_id="risk-toctou", value=Decimal("99.00"), key="risk-toctou-key"), PriceChangingAdapter())

    simulator = Simulator()
    awaiting = simulator.run(make_scenario(scenario_id="idem-confirm", confirmation="REQUIRED", key="idem-confirm-key"))
    confirmation = Confirmation.create(awaiting.quote)
    first = simulator.run(make_scenario(scenario_id="idem-confirm", confirmation="REQUIRED", key="idem-confirm-key"), quote=awaiting.quote, confirmation=confirmation)
    retry = simulator.run(make_scenario(scenario_id="idem-confirm", confirmation="REQUIRED", key="idem-confirm-key"), quote=awaiting.quote, confirmation=confirmation)
    new_key_old_confirmation = simulator.run(make_scenario(scenario_id="idem-confirm-new", confirmation="REQUIRED", key="idem-confirm-new-key"), quote=awaiting.quote, confirmation=confirmation)

    class PolicyDenyAfterPreviewAdapter(SyntheticExecutionAdapter):
        def __init__(self, policy: PolicyEngine) -> None:
            super().__init__(value=Decimal("10.00"), currency="USD")
            self.policy = policy

        def preview(self, scenario: Any) -> PreviewResult:
            preview = super().preview(scenario)
            self.policy.version = "2"
            return preview

    policy = PolicyEngine([PolicyRule("policy:flip", trust_class="CRYPTOGRAPHICALLY_VERIFIED", capability="cap:audit", environment="SANDBOX", decision=Decision.ALLOW, owner="audit")])
    policy_change = Simulator().run(make_scenario(scenario_id="policy-change", key="policy-change-key", policy=policy), PolicyDenyAfterPreviewAdapter(policy))

    class RevokingGrantAdapter(SyntheticExecutionAdapter):
        def preview(self, scenario: Any) -> PreviewResult:
            preview = super().preview(scenario)
            scenario.delegation = replace(scenario.delegation, revoked=True)
            return preview

    delegation_revocation = Simulator().run(make_scenario(scenario_id="delegation-revoke", key="delegation-revoke-key"), RevokingGrantAdapter(value=Decimal("10.00"), currency="USD"))
    return [
        case("risk_within_ceiling_still_requires_confirmation", confirmation_required.status.value == "AWAITING_CONFIRMATION", status=confirmation_required.status.value),
        case("risk_quote_toctou_blocks_changed_commit", toctou.status.value == "FAILED" and "TOCTOU_RESOURCE_CHANGED" in toctou.findings, status=toctou.status.value, findings=toctou.findings),
        case("idempotency_confirmation_retry_replays_one_effect", first.status.value == "EXECUTED" and retry.status.value == "EXECUTED", first=first.status.value, retry=retry.status.value, retry_findings=retry.findings),
        case("old_confirmation_new_key_rejected", new_key_old_confirmation.status.value == "FAILED" and "CONFIRMATION_REPLAY" in new_key_old_confirmation.findings, status=new_key_old_confirmation.status.value, findings=new_key_old_confirmation.findings),
        case("idempotency_claim_does_not_override_policy_recheck", policy_change.status.value == "DENIED" and "POLICY_CHANGED_BEFORE_COMMIT" in policy_change.findings, status=policy_change.status.value, findings=policy_change.findings),
        case("delegation_revocation_before_commit_fails_closed", delegation_revocation.status.value == "DENIED" and "POLICY_CHANGED_BEFORE_COMMIT" in delegation_revocation.findings, status=delegation_revocation.status.value, findings=delegation_revocation.findings),
    ]


def receipt_trace_tests() -> list[dict[str, Any]]:
    success = Simulator().run(make_scenario(scenario_id="receipt-success", key="receipt-success-key"))
    conflict_sim = Simulator()
    conflict_sim.run(make_scenario(scenario_id="receipt-conflict-a", key="receipt-conflict-key"))
    conflict = conflict_sim.run(make_scenario(scenario_id="receipt-conflict-b", key="receipt-conflict-key", value=Decimal("20.00")))
    denied = Simulator().run(make_scenario(scenario_id="receipt-denied", key="receipt-denied-key", value=Decimal("101.00")))
    dry = Simulator().run(make_scenario(scenario_id="receipt-dry", key="receipt-dry-key"), dry_run=True)
    engine = ReceiptEngine()
    return [
        case("receipt_success_valid_and_correlated", engine.verify(success.receipt).status == "VALID" and success.receipt.trace_id == success.trace["trace_id"], status=success.status.value, receipt_result=success.receipt.result),
        case("receipt_conflict_not_success", conflict.status.value == "FAILED" and conflict.receipt.result == "FAILED", status=conflict.status.value, findings=conflict.findings, receipt_result=conflict.receipt.result),
        case("receipt_denied_malformed_money_not_success", denied.status.value == "DENIED" and denied.receipt.result == "DENIED", status=denied.status.value, findings=denied.findings, receipt_result=denied.receipt.result),
        case("receipt_dry_run_side_effect_none", dry.status.value == "WOULD_ALLOW" and dry.receipt.result == "DRY_RUN" and dry.receipt.side_effect == "NONE", status=dry.status.value, receipt_result=dry.receipt.result, side_effect=dry.receipt.side_effect),
    ]


def manual_mutation_checks() -> list[dict[str, Any]]:
    risk_mut = Simulator().run(make_scenario(scenario_id="manual-risk-mutation", value=Decimal("100.01"), key="manual-risk-mutation-key"), controls=SimulatorControls(risk_ceiling_comparison=False))
    adapter = NonIdempotentCountingAdapter(sleep_seconds=0.005)
    simulator = Simulator()
    barrier = threading.Barrier(8)

    def run_one() -> str:
        barrier.wait(timeout=5)
        return simulator.run(make_scenario(scenario_id="manual-idem-mutation", key="manual-idem-mutation-key"), adapter, controls=SimulatorControls(idempotency_atomic_claim=False)).status.value

    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(lambda _: run_one(), range(8)))

    dry_adapter = InstrumentedDryRunAdapter(mutate_active=True)
    dry_mut = Simulator().run(make_scenario(scenario_id="manual-dry-mutation", key="manual-dry-mutation-key"), dry_adapter, dry_run=True, controls=SimulatorControls(dry_run_purity=False))
    return [
        case("manual_risk_mutation_tests_are_sensitive", risk_mut.status.value == "EXECUTED", mutated_status=risk_mut.status.value),
        case("manual_idempotency_mutation_tests_are_sensitive", adapter.side_effect_count > 1, side_effect_count=adapter.side_effect_count, statuses=statuses),
        case("manual_dryrun_mutation_tests_are_sensitive", dry_mut.status.value == "WOULD_ALLOW" and dry_adapter.counts["prepare"] > 0 and dry_adapter.counts["preview"] > 0, status=dry_mut.status.value, counts=dry_adapter.counts),
    ]


def process_local_limitation() -> dict[str, Any]:
    adapter = NonIdempotentCountingAdapter()
    first = Simulator().run(make_scenario(scenario_id="process-local", key="process-local-key"), adapter)
    second = Simulator().run(make_scenario(scenario_id="process-local", key="process-local-key"), adapter)
    return case("process_local_store_loses_claim_across_simulator_instances", first.status.value == "EXECUTED" and second.status.value == "EXECUTED" and adapter.side_effect_count == 2, first=first.status.value, second=second.status.value, side_effect_count=adapter.side_effect_count, classification="documented_reference_limitation")


def main() -> int:
    sections: dict[str, list[dict[str, Any]] | dict[str, Any]] = {}
    sections["money"] = money_retest()
    sections["concurrency"] = [concurrency_harness_a(8, 25), concurrency_harness_a(32, 10), concurrency_harness_b(), concurrency_harness_c()]
    sections["changed_request_conflicts"] = changed_request_conflicts()
    sections["request_hash_audit"] = [request_hash_audit()]
    sections["failure_recovery"] = failure_recovery_tests()
    sections["lost_response"] = [lost_response_test()]
    sections["dry_run"] = dry_run_tests()
    sections["cross_control"] = cross_control_tests()
    sections["receipt_trace"] = receipt_trace_tests()
    sections["manual_mutations"] = manual_mutation_checks()
    sections["process_local"] = [process_local_limitation()]

    all_checks = [item for value in sections.values() for item in value]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total": len(all_checks),
        "passed": sum(1 for item in all_checks if item["passed"]),
        "failed": [item for item in all_checks if not item["passed"]],
        "sections": sections,
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if not payload["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Run Phase 2C production-seam mutations; every critical control must be caught."""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier, Lock
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentnative.capabilities.models import Capability
from agentnative.delegation import DelegationGrant
from agentnative.identity import AgentIdentity, IntegrityResult, TrustClass
from agentnative.mutation import MutationCase, MutationHarness
from agentnative.observability import TraceContext
from agentnative.ownership import Environment, OwnershipVerification, VerificationStatus
from agentnative.policy import Decision, PolicyEngine, PolicyRule
from agentnative.protocols.models import ActionClass, SideEffect
from agentnative.receipts import ReceiptEngine
from agentnative.simulator import Scenario, Simulator, SimulatorControls, SyntheticExecutionAdapter
from agentnative.transactions import Confirmation, ExecutionResult, FailureClass, FailureInjection, FailurePoint, transaction_fingerprint


def scenario(*, environment=Environment.SANDBOX, confirmation="NONE", value=10.0, currency="USD", injections=(), compensation=False, key=None, policy=None, ownership=True, max_retries=2, grant_value_limit=100):
    now = datetime.now(timezone.utc)
    capability = Capability("cap:mutation", "business:mutation", "mutation action", action_class=ActionClass.CREATE, side_effect=SideEffect.REVERSIBLE)
    identity = AgentIdentity("agent:mutation", "provider:mutation", "Mutation Agent", TrustClass.CRYPTOGRAPHICALLY_VERIFIED)
    owner = OwnershipVerification("verification:mutation", "business:mutation", "sandbox", "fixture", "hash", now - timedelta(seconds=1), now + timedelta(hours=1), environment, VerificationStatus.VERIFIED, "fixture") if ownership else None
    grant = DelegationGrant("grant:mutation", "principal:mutation", identity.agent_id, identity.provider_id, frozenset({capability.capability_id}), resource_boundary="resource:synthetic", value_limit=grant_value_limit)
    rules = policy if policy is not None else [PolicyRule("allow-mutation", trust_class=identity.trust_class.value, capability=capability.capability_id, environment=environment.value, decision=Decision.ALLOW, owner="mutation")]
    return Scenario("scenario:mutation", "Phase 2C mutation scenario", "business:mutation", capability, environment, "principal:mutation", agent_identity=identity, integrity=IntegrityResult(True, "verified", "key:mutation", identity.agent_id, "nonce:mutation"), delegation=grant, ownership=owner, policy_engine=PolicyEngine(rules), confirmation_behavior=confirmation, value=value, currency=currency, resource_reference="resource:synthetic", failure_injections=injections, compensation_required=compensation, idempotency_key=key, max_retries=max_retries)


def receipt_values(secret=""):
    return dict(business_id="business", environment="SANDBOX", agent_id="agent", provider_id="provider", principal_reference=secret or "principal", capability_id="cap", policy_id="policy", policy_version="1", decision="ALLOW", delegation_reference="grant", confirmation_reference=None, quote_reference="quote", request_hash="a" * 64, result="EXECUTED", side_effect="REVERSIBLE", resource_reference="resource", value=10, currency="USD", correlation_id="correlation", trace_id="trace", evidence_refs=("policy_decided",))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    cases = []
    def risk_invariant(value, currency, controls):
        return Simulator().run(scenario(value=value, currency=currency, grant_value_limit=1000), controls=controls).status.value == "DENIED"

    cases.append(MutationCase("M2C-RISK-FINITE", "finite monetary validation", "bypass non-finite validation", lambda: risk_invariant(float("nan"), "USD", SimulatorControls()), lambda: risk_invariant(float("nan"), "USD", SimulatorControls(risk_value_validation=False))))
    cases.append(MutationCase("M2C-RISK-NEGATIVE", "non-negative monetary validation", "allow negative amount", lambda: risk_invariant(-1.0, "USD", SimulatorControls()), lambda: risk_invariant(-1.0, "USD", SimulatorControls(risk_value_validation=False))))
    cases.append(MutationCase("M2C-RISK-CURRENCY", "currency matching", "ignore currency mismatch", lambda: risk_invariant(10.0, "EUR", SimulatorControls()), lambda: risk_invariant(10.0, "EUR", SimulatorControls(risk_currency_validation=False))))
    cases.append(MutationCase("M2C-RISK-MISSING-CURRENCY", "currency presence", "treat missing currency as valid", lambda: risk_invariant(10.0, None, SimulatorControls()), lambda: risk_invariant(10.0, None, SimulatorControls(risk_currency_validation=False))))
    cases.append(MutationCase("M2C-RISK-CEILING", "inclusive monetary ceiling", "bypass ceiling comparison", lambda: risk_invariant(100.01, "USD", SimulatorControls()), lambda: risk_invariant(100.01, "USD", SimulatorControls(risk_ceiling_comparison=False))))
    cases.append(MutationCase("M2C-OWNERSHIP", "simulator ownership gate", "bypass ownership", lambda: Simulator().run(scenario(ownership=False)).status.value == "DENIED", lambda: Simulator().run(scenario(ownership=False), controls=SimulatorControls(owner_gate=False)).status.value == "DENIED"))
    cases.append(MutationCase("M2C-RISK", "environment risk ceiling", "allow above environment ceiling", lambda: Simulator().run(scenario(environment=Environment.PRODUCTION_READ_ONLY)).status.value == "DENIED", lambda: Simulator().run(scenario(environment=Environment.PRODUCTION_READ_ONLY), controls=SimulatorControls(risk_ceiling=False)).status.value == "DENIED"))
    cases.append(MutationCase("M2C-POLICY", "state-changing policy gate", "allow without policy", lambda: Simulator().run(scenario(policy=[])).status.value == "DENIED", lambda: Simulator().run(scenario(policy=[]), controls=SimulatorControls(policy_gate=False)).status.value == "DENIED"))
    cases.append(MutationCase("M2C-CONFIRMATION", "confirmation gate", "commit without required confirmation", lambda: Simulator().run(scenario(confirmation="REQUIRED")).status.value == "AWAITING_CONFIRMATION", lambda: Simulator().run(scenario(confirmation="REQUIRED"), controls=SimulatorControls(confirmation_gate=False)).status.value == "AWAITING_CONFIRMATION"))

    def binding_invariant(controls):
        awaiting = Simulator().run(scenario(confirmation="REQUIRED"))
        wrong = replace(Confirmation.create(awaiting.quote), principal_reference="other-principal")
        return Simulator().run(scenario(confirmation="REQUIRED"), confirmation=wrong, quote=awaiting.quote, controls=controls).status.value == "FAILED"
    cases.append(MutationCase("M2C-CONFIRMATION-BINDING", "confirmation binding", "disable context binding", lambda: binding_invariant(SimulatorControls()), lambda: binding_invariant(SimulatorControls(confirmation_binding=False))))

    def replay_invariant(controls):
        simulator = Simulator(); current = scenario(confirmation="REQUIRED")
        awaiting = simulator.run(current); confirmation = Confirmation.create(awaiting.quote)
        first = simulator.run(current, confirmation=confirmation, quote=awaiting.quote)
        replay = simulator.run(current, confirmation=confirmation, quote=awaiting.quote, controls=controls)
        names = [event["name"] for event in replay.trace["events"]]
        return first.status.value == "EXECUTED" and replay.status.value == "EXECUTED" and "result_replayed" in names and "confirmation_received" not in names
    cases.append(MutationCase("M-IDEM-CONFIRMATION-ORDER", "completed replay resolves before confirmation", "consume confirmation before idempotency replay", lambda: replay_invariant(SimulatorControls()), lambda: replay_invariant(SimulatorControls(idempotency_replay_resolution=False, confirmation_replay=False))))

    def competing_confirmation_invariant(controls):
        simulator = Simulator()
        current = scenario(confirmation="REQUIRED")
        awaiting = simulator.run(current)
        confirmation = Confirmation.create(awaiting.quote)
        winner = simulator.run(scenario(confirmation="REQUIRED", key="confirmation-owner-a"), confirmation=confirmation, quote=awaiting.quote, controls=controls)
        loser = simulator.run(scenario(confirmation="REQUIRED", key="confirmation-owner-b"), confirmation=confirmation, quote=awaiting.quote, controls=controls)
        return winner.status.value == "EXECUTED" and loser.status.value == "FAILED" and "CONFIRMATION_REPLAY" in loser.findings
    cases.append(MutationCase("M-CONFIRMATION-CROSS-TX-REUSE", "confirmation single-use across transactions", "allow one confirmation for two transactions", lambda: competing_confirmation_invariant(SimulatorControls()), lambda: competing_confirmation_invariant(SimulatorControls(confirmation_replay=False))))

    def material_dimension_invariant(dimension, changed):
        simulator = Simulator()
        base = scenario(key="material-dimension-key")
        simulator.run(base)
        result = simulator.run(changed(base))
        return result.status.value == "FAILED" and "IDEMPOTENCY_KEY_REUSE" in result.findings

    def omit_identity_dimension(dimension, changed):
        def omit(**kwargs):
            omitted = dict(kwargs)
            omitted[dimension] = None
            return transaction_fingerprint(**omitted)
        with patch("agentnative.simulator.models.transaction_fingerprint", omit):
            return material_dimension_invariant(dimension, changed)

    cases.append(MutationCase("M-IDEM-OMIT-PRINCIPAL", "principal is bound to fingerprint", "omit principal from fingerprint", lambda: material_dimension_invariant("principal_id", lambda base: replace(base, principal="principal:other")), lambda: omit_identity_dimension("principal_id", lambda base: replace(base, principal="principal:other"))))
    cases.append(MutationCase("M-IDEM-OMIT-AGENT", "agent is bound to fingerprint", "omit agent from fingerprint", lambda: material_dimension_invariant("agent_id", lambda base: replace(base, agent_identity=replace(base.agent_identity, agent_id="agent:other"), integrity=replace(base.integrity, agent_id="agent:other"))), lambda: omit_identity_dimension("agent_id", lambda base: replace(base, agent_identity=replace(base.agent_identity, agent_id="agent:other"), integrity=replace(base.integrity, agent_id="agent:other")))))
    cases.append(MutationCase("M-IDEM-OMIT-ENVIRONMENT", "environment is bound to fingerprint", "omit environment from fingerprint", lambda: material_dimension_invariant("environment", lambda base: replace(base, target_environment=Environment.STAGING, ownership=replace(base.ownership, environment=Environment.STAGING))), lambda: omit_identity_dimension("environment", lambda base: replace(base, target_environment=Environment.STAGING, ownership=replace(base.ownership, environment=Environment.STAGING)))))

    def expiry_invariant(controls):
        simulator = Simulator(); current = scenario(confirmation="REQUIRED")
        awaiting = simulator.run(current); confirmation = Confirmation.create(awaiting.quote)
        future = awaiting.quote.expires_at + timedelta(seconds=1)
        return simulator.run(current, confirmation=confirmation, quote=awaiting.quote, now=future, controls=controls).status.value == "FAILED"
    cases.append(MutationCase("M2C-QUOTE-EXPIRY", "quote and confirmation expiry", "accept expired quote", lambda: expiry_invariant(SimulatorControls()), lambda: expiry_invariant(SimulatorControls(quote_expiry=False))))
    cases.append(MutationCase("M2C-TOCTOU", "quote resource version", "ignore state change after preview", lambda: Simulator().run(scenario(injections=(FailureInjection(FailurePoint.AFTER_PREVIEW, "STALE_RESOURCE"),))).status.value == "FAILED", lambda: Simulator().run(scenario(injections=(FailureInjection(FailurePoint.AFTER_PREVIEW, "STALE_RESOURCE"),)), controls=SimulatorControls(toctou_detection=False)).status.value == "FAILED"))

    def idempotency_invariant(controls):
        adapter = SyntheticExecutionAdapter(failure_injections=(FailureInjection(FailurePoint.AFTER_COMMIT_BEFORE_RESPONSE, "RESPONSE_LOST"),))
        result = Simulator().run(scenario(), adapter, controls=controls)
        return result.status.value == "EXECUTED" and adapter.resource.version == 2
    cases.append(MutationCase("M2C-IDEMPOTENCY", "duplicate side-effect suppression", "disable idempotency", lambda: idempotency_invariant(SimulatorControls()), lambda: idempotency_invariant(SimulatorControls(idempotency=False))))

    def concurrent_idempotency_invariant(controls):
        class SlowCountingAdapter(SyntheticExecutionAdapter):
            def __init__(self):
                super().__init__(value=10)
                self.commit_count = 0
                self.commit_lock = Lock()

            def execute(self, current_scenario, quote, idempotency_key):
                time.sleep(0.01)
                with self.commit_lock:
                    self.commit_count += 1
                    self.resource.version += 1
                    version = str(self.resource.version)
                return ExecutionResult("SUCCESS", "mutation-concurrent-result", True, "REVERSIBLE", version)

        simulator = Simulator()
        adapter = SlowCountingAdapter()
        barrier = Barrier(8)

        def run_one():
            barrier.wait(timeout=5)
            return simulator.run(scenario(key="mutation-shared-key"), adapter, controls=controls).status.value

        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(lambda _: run_one(), range(8)))
        return adapter.commit_count == 1 and adapter.resource.version == 2 and statuses == ["EXECUTED"] * 8

    cases.append(MutationCase("M2C-IDEMPOTENCY-ATOMIC-CLAIM", "atomic idempotency reservation", "claim after execution", lambda: concurrent_idempotency_invariant(SimulatorControls()), lambda: concurrent_idempotency_invariant(SimulatorControls(idempotency_atomic_claim=False))))

    def hash_conflict_invariant(controls):
        simulator = Simulator()
        simulator.run(scenario(value=10, key="mutation-hash-key"), controls=controls)
        result = simulator.run(scenario(value=20, key="mutation-hash-key"), controls=controls)
        return result.status.value == "FAILED" and "IDEMPOTENCY_KEY_REUSE" in result.findings

    cases.append(MutationCase("M2C-IDEMPOTENCY-HASH-CONFLICT", "idempotency request-hash binding", "ignore same-key hash conflict", lambda: hash_conflict_invariant(SimulatorControls()), lambda: hash_conflict_invariant(SimulatorControls(idempotency_hash_conflict=False))))

    def dry_run_invariant(controls):
        class MutatingActiveAdapter(SyntheticExecutionAdapter):
            def prepare(self, current_scenario):
                self.resource.version += 1

            def preview(self, current_scenario):
                self.resource.version += 1
                return super().preview(current_scenario)

        adapter = MutatingActiveAdapter(value=10)
        before = adapter.snapshot()
        result = Simulator().run(scenario(), adapter, dry_run=True, controls=controls)
        return result.status.value == "WOULD_ALLOW" and before == adapter.snapshot()

    cases.append(MutationCase("M2C-DRYRUN-ACTIVE-PREVIEW", "dry-run plan isolation", "route dry-run to active preview", lambda: dry_run_invariant(SimulatorControls()), lambda: dry_run_invariant(SimulatorControls(dry_run_purity=False))))

    def retry_invariant(controls):
        result = Simulator().run(scenario(injections=(FailureInjection(FailurePoint.BEFORE_COMMIT, "TIMEOUT", FailureClass.RETRYABLE, 10),)), controls=controls)
        return result.attempts <= 3
    cases.append(MutationCase("M2C-RETRY-BOUND", "bounded retries", "permit excessive retry attempts", lambda: retry_invariant(SimulatorControls()), lambda: retry_invariant(SimulatorControls(bounded_retries=False))))
    cases.append(MutationCase("M2C-PARTIAL", "partial outcome representation", "convert PARTIAL to SUCCESS", lambda: Simulator().run(scenario(injections=(FailureInjection(FailurePoint.DURING_RESPONSE, "PARTIAL_SUCCESS"),))).status.value == "PARTIAL", lambda: Simulator().run(scenario(injections=(FailureInjection(FailurePoint.DURING_RESPONSE, "PARTIAL_SUCCESS"),)), controls=SimulatorControls(partial_outcome=False)).status.value == "PARTIAL"))
    cases.append(MutationCase("M2C-COMPENSATION", "compensation failure reporting", "hide failed compensation", lambda: "COMPENSATION_FAILED" in Simulator().run(scenario(injections=(FailureInjection(FailurePoint.DURING_RESPONSE, "PARTIAL_SUCCESS"), FailureInjection(FailurePoint.DURING_COMPENSATION, "COMPENSATION_FAILED")), compensation=True)).findings, lambda: "COMPENSATION_FAILED" in Simulator().run(scenario(injections=(FailureInjection(FailurePoint.DURING_RESPONSE, "PARTIAL_SUCCESS"), FailureInjection(FailurePoint.DURING_COMPENSATION, "COMPENSATION_FAILED")), compensation=True), controls=SimulatorControls(compensation_reporting=False)).findings))

    def receipt_invariant(engine):
        receipt = engine.create(**receipt_values())
        modified = {**receipt.to_dict(), "value": 999}
        return engine.verify(modified).status == "INVALID"
    cases.append(MutationCase("M2C-RECEIPT-INTEGRITY", "receipt integrity", "accept modified receipt", lambda: receipt_invariant(ReceiptEngine()), lambda: receipt_invariant(ReceiptEngine(integrity_enabled=False))))
    cases.append(MutationCase("M2C-TRACE-CORRELATION", "receipt trace correlation", "break trace identity", lambda: (lambda result: result.receipt.trace_id == result.trace["trace_id"])(Simulator().run(scenario(), trace_context=TraceContext.new())), lambda: (lambda result: result.receipt.trace_id == result.trace["trace_id"])(Simulator().run(scenario(), trace_context=TraceContext.new(), controls=SimulatorControls(trace_correlation=False)))))
    secret = "token=PHASE2C_MUTATION_SECRET_1234567890"
    cases.append(MutationCase("M2C-RECEIPT-REDACTION", "receipt secret minimization", "leak raw secret into receipt", lambda: secret not in repr(ReceiptEngine().create(**receipt_values(secret)).to_dict()), lambda: secret not in repr(ReceiptEngine(redaction_enabled=False).create(**receipt_values(secret)).to_dict())))

    results = MutationHarness().run(cases)
    payload = [{"mutation_id": item.mutation_id, "production_control": item.control, "mutation": item.mutation, "expected_test_failure": item.expected_test_failure, "actual_result": item.actual_result, "caught": item.caught} for item in results]
    rendered = json.dumps({"schema_version": "phase2c-mutation-results-1", "status": "PASS" if all(item["caught"] for item in payload) else "FAIL", "counts": {"total": len(payload), "killed": sum(item["caught"] for item in payload), "survived": sum(not item["caught"] for item in payload)}, "mutants": payload}, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        output = args.output if args.output.is_absolute() else Path(__file__).resolve().parents[1] / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if all(item["caught"] for item in payload) else 1


if __name__ == "__main__":
    raise SystemExit(main())

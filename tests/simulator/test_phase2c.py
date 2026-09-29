import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
import time

from agentnative.capabilities.models import Capability
from agentnative.delegation import DelegationGrant
from agentnative.identity import AgentIdentity, IntegrityResult, TrustClass
from agentnative.observability import TraceContext, TraceRecorder
from agentnative.ownership import Environment, OwnershipVerification, VerificationStatus
from agentnative.policy import Decision, PolicyEngine, PolicyRule
from agentnative.protocols.models import ActionClass, SideEffect
from agentnative.receipts import ReceiptEngine
from agentnative.simulator import Scenario, ScenarioState, ScenarioStateMachine, Simulator, SimulatorControls, SyntheticExecutionAdapter
from agentnative.transactions import Confirmation, ExecutionResult, FailureClass, FailureInjection, FailurePoint, Quote, TransactionSafetyError


class Phase2CFixture:
    def scenario(self, *, action=ActionClass.CREATE, confirmation="NONE", value=10.0, injections=(), compensation=False, key=None, policy=None, environment=Environment.SANDBOX, max_retries=2, input_data=None):
        now = datetime.now(timezone.utc)
        capability = Capability("cap:synthetic", "business:test", "synthetic action", action_class=action, side_effect=SideEffect.REVERSIBLE)
        identity = AgentIdentity("agent:test", "provider:test", "Test Agent", TrustClass.CRYPTOGRAPHICALLY_VERIFIED)
        ownership = OwnershipVerification("verification:test", "business:test", "sandbox.test", "fixture", "challenge", now - timedelta(seconds=1), now + timedelta(hours=1), environment, VerificationStatus.VERIFIED, "fixture")
        grant = DelegationGrant("grant:test", "principal:test", identity.agent_id, identity.provider_id, frozenset({capability.capability_id}), resource_boundary="resource:synthetic", value_limit=50, currency="USD")
        policy = policy or PolicyEngine([PolicyRule("allow-synthetic", trust_class=identity.trust_class.value, capability=capability.capability_id, environment=environment.value, decision=Decision.ALLOW, owner="tests")])
        return Scenario("scenario:test", "Synthetic controlled action", "business:test", capability, environment, "principal:test", input=input_data or {}, agent_identity=identity, integrity=IntegrityResult(True, "verified", "key:test", identity.agent_id, "nonce:test"), delegation=grant, ownership=ownership, policy_engine=policy, confirmation_behavior=confirmation, value=value, resource_reference="resource:synthetic", failure_injections=injections, compensation_required=compensation, idempotency_key=key, max_retries=max_retries)


class Phase2CSimulatorTests(unittest.TestCase, Phase2CFixture):
    def test_invalid_state_transition_is_rejected(self):
        machine = ScenarioStateMachine()
        with self.assertRaises(ValueError):
            machine.advance(ScenarioState.EXECUTING, "bypass")

    def test_happy_path_is_terminal_and_receipt_verifies(self):
        result = Simulator().run(self.scenario())
        self.assertEqual(result.status.value, "EXECUTED")
        self.assertEqual(result.state, ScenarioState.TERMINAL)
        self.assertEqual(ReceiptEngine().verify(result.receipt).status, "VALID")
        self.assertEqual(result.trace["trace_id"], result.receipt.trace_id)
        self.assertIn("policy_decided", [event["name"] for event in result.trace["events"]])

    def test_dry_run_does_not_change_adapter_state(self):
        adapter = SyntheticExecutionAdapter(resource_reference="resource:synthetic", value=10)
        before = adapter.snapshot()
        result = Simulator().run(self.scenario(), adapter, dry_run=True)
        self.assertEqual(result.status.value, "WOULD_ALLOW")
        self.assertEqual(adapter.snapshot(), before)

        required_before = adapter.snapshot()
        required = Simulator().run(self.scenario(confirmation="REQUIRED"), adapter, dry_run=True)
        self.assertEqual(required.status.value, "WOULD_REQUIRE_HUMAN")
        self.assertEqual(adapter.snapshot(), required_before)
        self.assertTrue(result.dry_run)

    def test_ownership_and_environment_risk_gates_deny_active_execution(self):
        scenario = self.scenario(environment=Environment.PRODUCTION_READ_ONLY)
        result = Simulator().run(scenario)
        self.assertEqual(result.status.value, "DENIED")
        self.assertIn("RISK_CEILING_EXCEEDED", result.findings)

    def test_confirmation_is_replay_safe_for_same_transaction_but_single_use_across_transactions(self):
        simulator = Simulator()
        awaiting = simulator.run(self.scenario(confirmation="REQUIRED"))
        self.assertEqual(awaiting.status.value, "AWAITING_CONFIRMATION")
        confirmation = Confirmation.create(awaiting.quote)
        executed = simulator.run(self.scenario(confirmation="REQUIRED"), confirmation=confirmation, quote=awaiting.quote)
        self.assertEqual(executed.status.value, "EXECUTED")
        replay = simulator.run(self.scenario(confirmation="REQUIRED"), confirmation=confirmation, quote=awaiting.quote)
        self.assertEqual(replay.status.value, "EXECUTED")
        self.assertEqual(replay.receipt.receipt_id, executed.receipt.receipt_id)
        competing = self.scenario(confirmation="REQUIRED", key="different-transaction")
        denied = simulator.run(competing, confirmation=confirmation, quote=awaiting.quote)
        self.assertEqual(denied.status.value, "FAILED")
        self.assertIn("CONFIRMATION_REPLAY", denied.findings)

    def test_response_loss_retries_without_duplicate_side_effect(self):
        adapter = SyntheticExecutionAdapter(failure_injections=(FailureInjection(FailurePoint.AFTER_COMMIT_BEFORE_RESPONSE, "RESPONSE_LOST"),))
        result = Simulator().run(self.scenario(), adapter)
        self.assertEqual(result.status.value, "EXECUTED")
        self.assertEqual(result.attempts, 2)
        self.assertEqual(adapter.resource.version, 2)

    def test_stale_quote_is_detected_before_commit(self):
        result = Simulator().run(self.scenario(injections=(FailureInjection(FailurePoint.AFTER_PREVIEW, "STALE_RESOURCE"),)))
        self.assertEqual(result.status.value, "FAILED")
        self.assertIn("TOCTOU_RESOURCE_CHANGED", result.findings)

    def test_partial_failure_can_be_compensated(self):
        result = Simulator().run(self.scenario(injections=(FailureInjection(FailurePoint.DURING_RESPONSE, "PARTIAL_SUCCESS"),), compensation=True))
        self.assertEqual(result.status.value, "COMPENSATED")
        self.assertTrue(any(event["name"] == "compensation_completed" for event in result.trace["events"]))

    def test_hidden_mutation_in_read_operation_is_critical(self):
        scenario = self.scenario(action=ActionClass.READ)
        result = Simulator().run(scenario, SyntheticExecutionAdapter(hidden_mutation=True))
        self.assertEqual(result.status.value, "FAILED")
        self.assertIn("CRITICAL_HIDDEN_MUTATION", result.findings)

    def test_policy_change_between_preview_and_commit_denies(self):
        policy = PolicyEngine([PolicyRule("allow-synthetic", trust_class="CRYPTOGRAPHICALLY_VERIFIED", capability="cap:synthetic", environment="SANDBOX", decision=Decision.ALLOW, owner="tests")])
        class PolicyChangingAdapter(SyntheticExecutionAdapter):
            def preview(self, scenario):
                result = super().preview(scenario)
                policy.version = "2"
                return result
        result = Simulator().run(self.scenario(policy=policy), PolicyChangingAdapter())
        self.assertEqual(result.status.value, "DENIED")
        self.assertIn("POLICY_CHANGED_BEFORE_COMMIT", result.findings)

    def test_cross_protocol_trace_keeps_one_root_identity(self):
        context = TraceContext.new("correlation:cross-protocol")
        recorder = TraceRecorder(context)
        recorder.emit("a2a_request", {"protocol": "A2A"})
        recorder.emit("mcp_tool_call", {"protocol": "MCP"})
        recorder.emit("http_openapi_commit", {"protocol": "OPENAPI"})
        result = Simulator().run(self.scenario(), trace_context=context, trace_recorder=recorder)
        self.assertEqual(result.trace["trace_id"], result.receipt.trace_id)
        self.assertEqual(result.trace["correlation_id"], result.receipt.correlation_id)
        names = [event["name"] for event in result.trace["events"]]
        self.assertTrue({"a2a_request", "mcp_tool_call", "http_openapi_commit"}.issubset(names))

    def test_trace_export_redacts_secret_attributes(self):
        recorder = TraceRecorder(TraceContext.new())
        recorder.emit("secret_test", {"authorization": "Bearer SECRET_TOKEN_1234567890"})
        exported = recorder.export()
        self.assertNotIn("SECRET_TOKEN_1234567890", repr(exported))

    def test_idempotency_key_reuse_for_different_request_is_rejected(self):
        simulator = Simulator()
        first = simulator.run(self.scenario(value=10, key="same-key"))
        self.assertEqual(first.status.value, "EXECUTED")
        second = simulator.run(self.scenario(value=20, key="same-key"))
        self.assertEqual(second.status.value, "FAILED")
        self.assertIn("IDEMPOTENCY_KEY_REUSE", second.findings)

    def test_material_transaction_identity_dimensions_fail_closed(self):
        simulator = Simulator()
        base = self.scenario(key="material-identity-key")
        self.assertEqual(simulator.run(base).status.value, "EXECUTED")
        changed = {
            "principal": "principal:other",
            "business_id": "business:other",
            "target_environment": Environment.STAGING,
            "resource_reference": "resource:other",
            "value": 11,
            "currency": "CAD",
            "input": {"material": "changed"},
        }
        for field, value in changed.items():
            candidate = replace(base, **{field: value})
            if field == "target_environment":
                candidate = replace(candidate, ownership=replace(base.ownership, environment=value))
            result = simulator.run(candidate)
            self.assertNotEqual(result.status.value, "EXECUTED", field)
            self.assertIn("IDEMPOTENCY_KEY_REUSE", result.findings, field)

    def test_agent_provider_capability_quote_and_confirmation_identity_fail_closed(self):
        simulator = Simulator()
        base = self.scenario(key="identity-dimension-key")
        self.assertEqual(simulator.run(base).status.value, "EXECUTED")
        changed_identity = replace(base.agent_identity, agent_id="agent:other")
        changed_agent = replace(base, agent_identity=changed_identity, integrity=replace(base.integrity, agent_id="agent:other"))
        self.assertIn("IDEMPOTENCY_KEY_REUSE", simulator.run(changed_agent).findings)
        changed_provider = replace(base, agent_identity=replace(base.agent_identity, provider_id="provider:other"))
        self.assertIn("IDEMPOTENCY_KEY_REUSE", simulator.run(changed_provider).findings)
        changed_capability = replace(base, capability=replace(base.capability, capability_id="cap:other"))
        self.assertIn("IDEMPOTENCY_KEY_REUSE", simulator.run(changed_capability).findings)

        quote_awaiting = simulator.run(self.scenario(key="quote-identity-key", confirmation="REQUIRED"))
        quote_one = quote_awaiting.quote
        self.assertIsNotNone(quote_one)
        quote_confirmation = Confirmation.create(quote_one)
        first = simulator.run(self.scenario(key="quote-identity-key", confirmation="REQUIRED"), quote=quote_one, confirmation=quote_confirmation)
        self.assertEqual(first.status.value, "EXECUTED")
        quote_two = Quote.create(capability_id=quote_one.capability_id, resource_reference=quote_one.resource_reference, value=quote_one.value, currency=quote_one.currency, terms={"changed": True}, version=quote_one.version, principal_reference=quote_one.principal_reference, business_id=quote_one.business_id, environment=quote_one.environment)
        conflict = simulator.run(self.scenario(key="quote-identity-key", confirmation="REQUIRED"), quote=quote_two, confirmation=quote_confirmation)
        self.assertIn("IDEMPOTENCY_KEY_REUSE", conflict.findings)

        confirmed_key = "confirmation-identity-key"
        awaiting = simulator.run(self.scenario(key=confirmed_key, confirmation="REQUIRED"))
        confirmation_one = Confirmation.create(awaiting.quote)
        self.assertEqual(simulator.run(self.scenario(key=confirmed_key, confirmation="REQUIRED"), quote=awaiting.quote, confirmation=confirmation_one).status.value, "EXECUTED")
        confirmation_two = Confirmation.create(awaiting.quote)
        conflict = simulator.run(self.scenario(key=confirmed_key, confirmation="REQUIRED"), quote=awaiting.quote, confirmation=confirmation_two)
        self.assertIn("IDEMPOTENCY_KEY_REUSE", conflict.findings)

    def test_non_material_trace_metadata_does_not_change_replay_identity(self):
        simulator = Simulator()
        scenario = self.scenario(key="metadata-replay-key")
        first = simulator.run(scenario, trace_context=TraceContext.new("transport:first"))
        second = simulator.run(scenario, trace_context=TraceContext.new("transport:retry"))
        self.assertEqual(first.status.value, "EXECUTED")
        self.assertEqual(second.status.value, "EXECUTED")
        self.assertEqual(first.receipt.receipt_id, second.receipt.receipt_id)
        self.assertTrue(any(event["name"] == "result_replayed" for event in second.trace["events"]))

    def test_same_confirmed_transaction_concurrency_binds_once_and_replays(self):
        class SlowCountingAdapter(SyntheticExecutionAdapter):
            def __init__(self):
                super().__init__(value=10)
                self.commit_count = 0
                self.commit_lock = Lock()

            def execute(self, scenario, quote, idempotency_key):
                time.sleep(0.02)
                with self.commit_lock:
                    self.commit_count += 1
                    self.resource.version += 1
                    version = str(self.resource.version)
                return ExecutionResult("SUCCESS", "confirmed-concurrent-result", True, "REVERSIBLE", version)

        simulator = Simulator()
        scenario = self.scenario(key="confirmed-concurrent-key", confirmation="REQUIRED")
        awaiting = simulator.run(scenario)
        confirmation = Confirmation.create(awaiting.quote)
        adapter = SlowCountingAdapter()

        def run_one():
            return simulator.run(scenario, adapter, quote=awaiting.quote, confirmation=confirmation).status.value

        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(lambda _: run_one(), range(8)))
        self.assertEqual(adapter.commit_count, 1)
        self.assertEqual(len(simulator.transactions.confirmation_bindings), 1)
        self.assertEqual(statuses, ["EXECUTED"] * 8)

    def test_distinct_transactions_compete_for_one_confirmation(self):
        simulator = Simulator()
        awaiting = simulator.run(self.scenario(confirmation="REQUIRED"))
        confirmation = Confirmation.create(awaiting.quote)
        scenarios = [self.scenario(key="confirmation-owner-a", confirmation="REQUIRED"), self.scenario(key="confirmation-owner-b", confirmation="REQUIRED")]

        def run_one(item):
            return simulator.run(item, quote=awaiting.quote, confirmation=confirmation)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run_one, scenarios))
        self.assertEqual(sum(result.status.value == "EXECUTED" for result in results), 1)
        self.assertEqual(sum("CONFIRMATION_REPLAY" in result.findings for result in results), 1)

    def test_completed_replay_after_confirmation_expiry_returns_original_result(self):
        simulator = Simulator()
        scenario = self.scenario(key="expired-replay-key", confirmation="REQUIRED")
        awaiting = simulator.run(scenario)
        confirmation = Confirmation.create(awaiting.quote, ttl=timedelta(seconds=1))
        executed = simulator.run(scenario, quote=awaiting.quote, confirmation=confirmation)
        replay = simulator.run(scenario, quote=awaiting.quote, confirmation=confirmation, now=confirmation.expires_at + timedelta(seconds=1))
        self.assertEqual(replay.status.value, "EXECUTED")
        self.assertEqual(replay.receipt.receipt_id, executed.receipt.receipt_id)
        self.assertNotIn("CONFIRMATION_REPLAY", replay.findings)

    def test_unknown_outcome_never_blindly_reexecutes(self):
        class UnknownOutcomeAdapter(SyntheticExecutionAdapter):
            def execute(self, scenario, quote, idempotency_key):
                raise TransactionSafetyError("DOWNSTREAM_UNKNOWN", "downstream response was lost", FailureClass.UNKNOWN, state_changed=True)

        simulator = Simulator()
        scenario = self.scenario(key="unknown-outcome-key")
        first = simulator.run(scenario, UnknownOutcomeAdapter())
        second_adapter = UnknownOutcomeAdapter()
        second = simulator.run(scenario, second_adapter)
        self.assertEqual(first.status.value, "PARTIAL")
        self.assertEqual(second.status.value, "FAILED")
        self.assertIn("IDEMPOTENCY_UNKNOWN_OUTCOME", second.findings)

    def test_retryable_failure_reuses_same_logical_confirmation_binding(self):
        class RetryableBeforeSideEffectAdapter(SyntheticExecutionAdapter):
            def __init__(self):
                super().__init__(value=10)

            def execute(self, scenario, quote, idempotency_key):
                raise TransactionSafetyError("TEMPORARY_DOWNSTREAM", "temporary failure", FailureClass.RETRYABLE)

        simulator = Simulator()
        scenario = self.scenario(key="retryable-confirmation-key", confirmation="REQUIRED", max_retries=0)
        awaiting = simulator.run(scenario)
        confirmation = Confirmation.create(awaiting.quote)
        first = simulator.run(scenario, RetryableBeforeSideEffectAdapter(), quote=awaiting.quote, confirmation=confirmation)
        second = simulator.run(scenario, quote=awaiting.quote, confirmation=confirmation)
        self.assertEqual(first.status.value, "FAILED")
        self.assertEqual(second.status.value, "EXECUTED")
        self.assertEqual(len(simulator.transactions.confirmation_bindings), 1)

    def test_concurrent_same_key_has_one_logical_side_effect(self):
        class SlowCountingAdapter(SyntheticExecutionAdapter):
            def __init__(self):
                super().__init__(value=10)
                self.commit_count = 0
                self.commit_lock = Lock()

            def execute(self, scenario, quote, idempotency_key):
                time.sleep(0.02)
                with self.commit_lock:
                    self.commit_count += 1
                    self.resource.version += 1
                    version = str(self.resource.version)
                return ExecutionResult("SUCCESS", "concurrent-result", True, "REVERSIBLE", version)

        for round_number in range(25):
            simulator = Simulator()
            adapter = SlowCountingAdapter()
            start = Barrier(8)

            def run_one():
                start.wait(timeout=5)
                return simulator.run(self.scenario(key=f"shared-concurrent-key-{round_number}"), adapter).status.value

            with ThreadPoolExecutor(max_workers=8) as pool:
                statuses = list(pool.map(lambda _: run_one(), range(8)))
            self.assertEqual(adapter.commit_count, 1)
            self.assertEqual(adapter.resource.version, 2)
            self.assertEqual(statuses, ["EXECUTED"] * 8)

    def test_dry_run_skips_active_prepare_and_preview(self):
        class MutatingActiveAdapter(SyntheticExecutionAdapter):
            def prepare(self, scenario):
                self.resource.version += 1

            def preview(self, scenario):
                self.resource.version += 1
                return super().preview(scenario)

        adapter = MutatingActiveAdapter(value=10)
        before = adapter.snapshot()
        result = Simulator().run(self.scenario(), adapter, dry_run=True)
        self.assertEqual(result.status.value, "WOULD_ALLOW")
        self.assertEqual(adapter.snapshot(), before)

    def test_dry_run_fails_closed_if_safe_plan_mutates(self):
        class MutatingPlanAdapter(SyntheticExecutionAdapter):
            def build_plan(self, scenario):
                self.resource.version += 1
                return super().build_plan(scenario)

        result = Simulator().run(self.scenario(), MutatingPlanAdapter(value=10), dry_run=True)
        self.assertEqual(result.status.value, "WOULD_DENY")
        self.assertIn("DRY_RUN_SIDE_EFFECT", result.findings)

    def test_mutation_controls_are_not_defaulted_off(self):
        result = Simulator().run(self.scenario(), controls=SimulatorControls())
        self.assertEqual(result.status.value, "EXECUTED")


if __name__ == "__main__":
    unittest.main()

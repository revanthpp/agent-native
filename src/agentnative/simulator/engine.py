from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from agentnative.observability import TraceContext, TraceRecorder
from agentnative.policy import Decision, PolicyDecision, PolicyEngine, authorize_state_change
from agentnative.protocols.models import ActionClass
from agentnative.receipts import Receipt, ReceiptEngine
from agentnative.simulator.adapters import SyntheticExecutionAdapter
from agentnative.simulator.models import Scenario, SimulationResult, SimulationStatus
from agentnative.simulator.state import ScenarioState, ScenarioStateMachine
from agentnative.transactions import (
    Confirmation,
    FailureClass,
    FailurePoint,
    ExecutionResult,
    IdempotencyStatus,
    PreviewResult,
    Quote,
    TransactionSafetyEngine,
    TransactionSafetyError,
    default_risk_ceiling,
)


@dataclass(frozen=True)
class SimulatorControls:
    """Explicit production seams used by the Phase 2C mutation harness."""

    owner_gate: bool = True
    risk_ceiling: bool = True
    risk_value_validation: bool = True
    risk_currency_validation: bool = True
    risk_ceiling_comparison: bool = True
    policy_gate: bool = True
    confirmation_gate: bool = True
    confirmation_binding: bool = True
    confirmation_replay: bool = True
    quote_expiry: bool = True
    toctou_detection: bool = True
    idempotency: bool = True
    bounded_retries: bool = True
    partial_outcome: bool = True
    compensation_reporting: bool = True
    trace_correlation: bool = True
    idempotency_atomic_claim: bool = True
    idempotency_hash_conflict: bool = True
    idempotency_replay_resolution: bool = True
    dry_run_purity: bool = True


class Simulator:
    """Fail-closed Phase 2C lifecycle coordinator for controlled adapters."""

    def __init__(self, *, receipt_engine: ReceiptEngine | None = None) -> None:
        self.receipts = receipt_engine or ReceiptEngine()
        self.transactions = TransactionSafetyEngine()

    def run(self, scenario: Scenario, adapter: Any | None = None, *, dry_run: bool = False, confirmation: Confirmation | None = None, quote: Quote | None = None, trace_context: TraceContext | None = None, trace_recorder: TraceRecorder | None = None, now: datetime | None = None, controls: SimulatorControls | None = None) -> SimulationResult:
        clock = now or datetime.now(timezone.utc)
        controls = controls or SimulatorControls()
        run_id = "run-" + uuid4().hex[:24]
        context = trace_context or TraceContext.new()
        trace = trace_recorder or TraceRecorder(context, common_attributes={"scenario_id": scenario.scenario_id, "capability_id": scenario.capability.capability_id, "agent_id": scenario.agent_identity.agent_id if scenario.agent_identity else None, "business_id": scenario.business_id, "environment": scenario.target_environment.value})
        machine = ScenarioStateMachine()
        tx = self.transactions
        tx.max_retries = max(0, scenario.max_retries)
        ceiling = default_risk_ceiling(scenario.target_environment)
        policy = scenario.policy_engine or PolicyEngine([])
        selected_adapter = adapter or SyntheticExecutionAdapter(failure_injections=tuple(item for item in scenario.failure_injections if item.point in {FailurePoint.AFTER_COMMIT_BEFORE_RESPONSE, FailurePoint.DURING_RESPONSE, FailurePoint.DURING_COMPENSATION}), resource_reference=scenario.resource_reference, value=scenario.value, currency=scenario.currency)
        pending = list(scenario.failure_injections)
        decision = "UNKNOWN"
        policy_version_at_preview = getattr(policy, "version", "unknown")
        message = ""
        findings: list[str] = []
        limitations: list[str] = []
        active_quote = quote
        quote_was_supplied = quote is not None
        active_confirmation = confirmation
        attempts = 0
        # The generated key uses the stable request identity without quote or
        # confirmation IDs. Explicit quote/confirmation references are added
        # to the fingerprint only once they are part of the committed request.
        idempotency_key = scenario.idempotency_key or f"{scenario.scenario_id}:{scenario.request_hash[:16]}"
        request_hash = scenario.request_hash
        logical_id = tx.logical_transaction_id(idempotency_key, request_hash)
        idempotency_claimed = False
        idempotency_preclaimed = False
        idempotency_finalized = False
        idempotency_failure_status: str | None = None
        replayed_receipt: Receipt | None = None
        replay_resolution = False
        idempotency_result_reference: str | None = None

        trace.emit("simulation_started", {"run_id": run_id, "dry_run": dry_run})

        def move(target: ScenarioState, reason: str) -> None:
            transition = machine.advance(target, reason)
            trace.emit("state_transition", {"from_state": transition.from_state.value, "to_state": transition.to_state.value, "reason": reason})

        def consume(point: FailurePoint) -> None:
            for index, injection in enumerate(pending):
                if injection.point != point or injection.occurrences <= 0:
                    continue
                pending[index] = type(injection)(injection.point, injection.failure_type, injection.failure_class, injection.occurrences - 1)
                if point == FailurePoint.AFTER_PREVIEW and injection.failure_type.upper() in {"STALE_RESOURCE", "RESOURCE_CHANGED", "PRICE_CHANGED"} and hasattr(selected_adapter, "mutate_external"):
                    selected_adapter.mutate_external()
                    trace.emit("failure_injected", {"point": point.value, "failure_type": injection.failure_type})
                    return
                raise TransactionSafetyError("INJECTED_" + injection.failure_type.upper(), f"controlled failure injection: {injection.failure_type}", injection.failure_class)

        def finish(status: SimulationStatus, final_message: str, *, current_quote: Quote | None = None, current_confirmation: Confirmation | None = None, side_effect: str = "NONE", result: str | None = None) -> SimulationResult:
            nonlocal active_quote, active_confirmation, message, idempotency_finalized
            if current_quote is not None:
                active_quote = current_quote
            if current_confirmation is not None:
                active_confirmation = current_confirmation
            message = final_message
            if controls.idempotency and idempotency_claimed and not idempotency_finalized:
                if idempotency_failure_status:
                    claim_status = idempotency_failure_status
                elif status in {SimulationStatus.EXECUTED, SimulationStatus.COMPENSATED}:
                    claim_status = IdempotencyStatus.SUCCEEDED.value
                elif status == SimulationStatus.PARTIAL or side_effect != "NONE":
                    claim_status = IdempotencyStatus.UNKNOWN_OUTCOME.value
                else:
                    claim_status = IdempotencyStatus.FAILED_TERMINAL.value
                tx.record_idempotency(idempotency_key, request_hash, claim_status, idempotency_result_reference or result, error_reference=findings[-1] if findings and claim_status != IdempotencyStatus.SUCCEEDED.value else None, logical_id=logical_id)
                idempotency_finalized = True
            if machine.state != ScenarioState.RECEIPT_CREATED and machine.state != ScenarioState.TERMINAL:
                if machine.can_transition(ScenarioState.RECEIPT_CREATED):
                    move(ScenarioState.RECEIPT_CREATED, "simulation evidence finalized")
                else:
                    # All execution paths must pass through a terminal outcome.
                    if machine.can_transition(ScenarioState.FAILED):
                        move(ScenarioState.FAILED, "simulation finalized after an incomplete path")
                    move(ScenarioState.RECEIPT_CREATED, "simulation evidence finalized")
            receipt: Receipt | None = replayed_receipt
            if machine.state != ScenarioState.TERMINAL and receipt is None:
                receipt = self.receipts.create(
                    business_id=scenario.business_id,
                    environment=scenario.target_environment.value,
                    agent_id=scenario.agent_identity.agent_id if scenario.agent_identity else "unknown",
                    provider_id=scenario.agent_identity.provider_id if scenario.agent_identity else "unknown",
                    principal_reference=scenario.principal,
                    capability_id=scenario.capability.capability_id,
                    policy_id=getattr(getattr(policy, "rules", [None])[0], "policy_id", None) if getattr(policy, "rules", None) else None,
                    policy_version=getattr(policy, "version", "unknown"),
                    decision=decision,
                    delegation_reference=scenario.delegation.grant_id if scenario.delegation else None,
                    confirmation_reference=active_confirmation.confirmation_id if active_confirmation else None,
                    quote_reference=active_quote.quote_id if active_quote else None,
                    request_hash=request_hash,
                    result=result or status.value,
                    side_effect=side_effect,
                    resource_reference=scenario.resource_reference,
                    value=scenario.value,
                    currency=scenario.currency,
                    correlation_id=context.correlation_id if controls.trace_correlation else "correlation-broken",
                    trace_id=context.trace_id if controls.trace_correlation else "trace-broken",
                    evidence_refs=tuple(event.name for event in trace.events),
                )
                trace.emit("receipt_created", {"receipt_id": receipt.receipt_id})
                if controls.idempotency and idempotency_claimed:
                    tx.attach_receipt(idempotency_key, request_hash, receipt)
                if machine.can_transition(ScenarioState.TERMINAL):
                    move(ScenarioState.TERMINAL, "receipt created")
            trace.emit("simulation_completed", {"status": status.value, "run_id": run_id})
            if receipt is not None and machine.can_transition(ScenarioState.TERMINAL):
                move(ScenarioState.TERMINAL, "receipt reference resolved")
            return SimulationResult(run_id, scenario.scenario_id, status, machine.state, decision, final_message, machine.trace(), findings, limitations, active_quote, active_confirmation, receipt, trace.export(), attempts, idempotency_key, dry_run)

        def fail(status: SimulationStatus, final_message: str, finding: str, *, side_effect: str = "NONE") -> SimulationResult:
            findings.append(finding)
            if machine.state not in {ScenarioState.FAILED, ScenarioState.PARTIAL, ScenarioState.COMPENSATING} and machine.can_transition(ScenarioState.FAILED):
                move(ScenarioState.FAILED, final_message)
            return finish(status, final_message, side_effect=side_effect, result=status.value)

        def replay_completed(record: Any) -> SimulationResult:
            """Return the original outcome without re-consuming confirmation or executing."""
            nonlocal replayed_receipt, replay_resolution, idempotency_result_reference, decision
            replay_resolution = True
            idempotency_result_reference = record.result_reference
            replayed_receipt = tx.get_receipt(idempotency_key, request_hash, wait_timeout=scenario.timeout_seconds)
            trace.emit("idempotency_replay_detected", {"logical_transaction_id": record.logical_transaction_id or logical_id, "result_reference": record.result_reference})
            trace.emit("existing_transaction_resolved", {"status": record.status, "receipt_reference": record.receipt_reference})
            trace.emit("result_replayed", {"side_effect": "NONE", "original_receipt": record.receipt_reference})
            decision = Decision.ALLOW.value
            for target, reason in (
                (ScenarioState.DELEGATION_VERIFIED, "replay actor context resolved"),
                (ScenarioState.CAPABILITY_RESOLVED, "replay capability identity resolved"),
                (ScenarioState.POLICY_EVALUATED, "completed replay does not re-evaluate policy"),
                (ScenarioState.PREVIEWED, "completed replay uses the stored transaction"),
                (ScenarioState.AUTHORIZED, "stored authorization applies to replay"),
                (ScenarioState.EXECUTING, "replay resolved without starting execution"),
                (ScenarioState.EXECUTED, "stored execution outcome replayed"),
                (ScenarioState.VERIFYING, "stored outcome verification replayed"),
                (ScenarioState.SUCCEEDED, "stored outcome was successful"),
            ):
                if machine.can_transition(target):
                    move(target, reason)
            return finish(SimulationStatus.EXECUTED, "idempotent transaction result replayed", side_effect="NONE", result="EXECUTED")

        try:
            ownership_valid = not controls.owner_gate or (scenario.ownership is not None and scenario.ownership.is_valid(clock) and scenario.ownership.environment == scenario.target_environment)
            if not ownership_valid:
                decision = Decision.DENY.value
                return fail(SimulationStatus.WOULD_DENY if dry_run else SimulationStatus.DENIED, "verified ownership is required before active simulation", "OWNER_VERIFICATION_REQUIRED")
            move(ScenarioState.OWNER_VERIFIED, "ownership verification is valid")
            trace.emit("ownership_verified", {"verification_id": scenario.ownership.verification_id})

            identity = scenario.agent_identity
            integrity = scenario.integrity
            if identity is None or integrity is None or not integrity.valid or integrity.agent_id != identity.agent_id or identity.trust_class.value in {"UNKNOWN", "DECLARED"}:
                decision = Decision.DENY.value
                return fail(SimulationStatus.WOULD_DENY if dry_run else SimulationStatus.DENIED, "cryptographically verified agent identity is required", "AGENT_VERIFICATION_REQUIRED")
            move(ScenarioState.AGENT_VERIFIED, "agent identity and request integrity are valid")
            trace.emit("identity_verified", {"identity_method": identity.identity_method})

            # Resolve completed replays immediately after actor identity is
            # authenticated. This is intentionally before policy/delegation
            # re-consumption and before confirmation consumption: no current
            # authorization evidence can turn a completed replay into a new
            # business action, and no confirmation token is consumed twice.
            if controls.idempotency and controls.idempotency_replay_resolution:
                preflight_hash = scenario.transaction_fingerprint(
                    quote_id=quote.quote_id if quote is not None else None,
                    confirmation_id=active_confirmation.confirmation_id if active_confirmation is not None else None,
                )
                preflight_record = tx.lookup_idempotency(idempotency_key, preflight_hash, enforce_hash=controls.idempotency_hash_conflict)
                if preflight_record and preflight_record.status == IdempotencyStatus.SUCCEEDED.value:
                    request_hash = preflight_hash
                    logical_id = preflight_record.logical_transaction_id or tx.logical_transaction_id(idempotency_key, request_hash)
                    return replay_completed(preflight_record)

            if scenario.delegation is None:
                decision = Decision.DENY.value
                return fail(SimulationStatus.WOULD_DENY if dry_run else SimulationStatus.DENIED, "delegation is required before simulation", "DELEGATION_REQUIRED")
            move(ScenarioState.DELEGATION_VERIFIED, "delegation reference is present")
            trace.emit("delegation_verified", {"delegation_id": scenario.delegation.grant_id})
            move(ScenarioState.CAPABILITY_RESOLVED, "capability resolved from scenario")
            trace.emit("capability_resolved", {"action_class": scenario.capability.action_class.value})

            allowed, ceiling_reason = (True, "risk ceiling control disabled") if not controls.risk_ceiling else ceiling.allows(scenario.capability.action_class, scenario.value, scenario.currency, validate_value=controls.risk_value_validation, validate_currency=controls.risk_currency_validation, enforce_ceiling=controls.risk_ceiling_comparison)
            if not allowed:
                decision = Decision.DENY.value
                finding = ceiling_reason if ceiling_reason.startswith("RISK_") else "RISK_CEILING_EXCEEDED"
                return fail(SimulationStatus.WOULD_DENY if dry_run else SimulationStatus.DENIED, ceiling_reason, finding)
            consume(FailurePoint.BEFORE_POLICY)
            context_data = {"principal": scenario.principal, "audience": scenario.audience, "resource": scenario.resource_reference, "value": scenario.value, "currency": scenario.currency, "environment": scenario.target_environment.value, "policy_version": policy.version}
            policy_decision = authorize_state_change(owner_verified=True, identity=identity, integrity=integrity, grant=scenario.delegation, capability=scenario.capability, engine=policy, context=context_data) if controls.policy_gate else PolicyDecision(Decision.ALLOW, None, policy.version, "policy gate disabled")
            decision = policy_decision.decision.value
            policy_version_at_preview = policy_decision.policy_version
            trace.emit("policy_decided", {"decision": decision, "policy_version": policy_decision.policy_version, "reason": policy_decision.reason})
            move(ScenarioState.POLICY_EVALUATED, policy_decision.reason)
            requires_confirmation = controls.confirmation_gate and (scenario.requires_confirmation or policy_decision.decision == Decision.REQUIRE_HUMAN)
            if policy_decision.decision == Decision.DENY:
                return fail(SimulationStatus.WOULD_DENY if dry_run else SimulationStatus.DENIED, policy_decision.reason, "POLICY_DENIED")

            consume(FailurePoint.BEFORE_PREVIEW)
            if dry_run and controls.dry_run_purity:
                before_plan_snapshot = selected_adapter.snapshot()
                build_plan = getattr(selected_adapter, "build_plan", None)
                if callable(build_plan):
                    preview = build_plan(scenario)
                else:
                    limitations.append("REMOTE_PREVIEW_NOT_EXECUTED_IN_DRY_RUN")
                    preview = PreviewResult(scenario.resource_reference, "local-plan", scenario.value, scenario.currency, {"local_plan": True, "remote_preview": "NOT_EXECUTED_IN_DRY_RUN"})
                after_plan_snapshot = selected_adapter.snapshot()
                if before_plan_snapshot != after_plan_snapshot:
                    raise TransactionSafetyError("DRY_RUN_SIDE_EFFECT", "dry-run planning changed adapter-visible state", FailureClass.TERMINAL, state_changed=True)
            elif dry_run:
                selected_adapter.prepare(scenario)
                preview = selected_adapter.preview(scenario)
            else:
                selected_adapter.prepare(scenario)
                preview = selected_adapter.preview(scenario)
            preview_allowed, preview_reason = (True, "risk ceiling control disabled") if not controls.risk_ceiling else ceiling.allows(scenario.capability.action_class, preview.value, preview.currency, validate_value=controls.risk_value_validation, validate_currency=controls.risk_currency_validation, enforce_ceiling=controls.risk_ceiling_comparison)
            if not preview_allowed:
                finding = preview_reason if preview_reason.startswith("RISK_") else "RISK_CEILING_EXCEEDED"
                decision = Decision.DENY.value
                return fail(SimulationStatus.WOULD_DENY if dry_run else SimulationStatus.DENIED, preview_reason, finding)
            if active_quote is None:
                active_quote = Quote.create(capability_id=scenario.capability.capability_id, resource_reference=preview.resource_reference, value=preview.value, currency=preview.currency, terms=preview.terms, version=preview.resource_version, principal_reference=scenario.principal, business_id=scenario.business_id, environment=scenario.target_environment, evidence_refs=(f"scenario:{scenario.scenario_id}",))
            request_hash = scenario.transaction_fingerprint(
                quote_id=active_quote.quote_id if quote_was_supplied else None,
                confirmation_id=active_confirmation.confirmation_id if active_confirmation is not None else None,
            )
            logical_id = tx.logical_transaction_id(idempotency_key, request_hash)
            if not dry_run:
                consume(FailurePoint.AFTER_PREVIEW)
            trace.emit("preview_created", {"quote_id": active_quote.quote_id, "quote_version": active_quote.version})
            move(ScenarioState.PREVIEWED, "preview and quote created")
            if dry_run:
                preview_context = {**context_data, "value": preview.value, "currency": preview.currency}
                preview_policy = authorize_state_change(owner_verified=True, identity=identity, integrity=integrity, grant=scenario.delegation, capability=scenario.capability, engine=policy, context=preview_context) if controls.policy_gate else PolicyDecision(Decision.ALLOW, None, policy.version, "policy gate disabled")
                if preview_policy.decision == Decision.DENY:
                    decision = Decision.DENY.value
                    return fail(SimulationStatus.WOULD_DENY, preview_policy.reason, "POLICY_DENIED")
                if requires_confirmation:
                    move(ScenarioState.AWAITING_CONFIRMATION, "confirmation would be required")
                    return finish(SimulationStatus.WOULD_REQUIRE_HUMAN, "human confirmation would be required", result="DRY_RUN")
                return finish(SimulationStatus.WOULD_ALLOW, "policy and transaction controls would allow execution", result="DRY_RUN")

            # Reserve the logical transaction before consuming confirmation or
            # entering the adapter. A missing confirmation is a preflight
            # response, so it deliberately does not create a PENDING record.
            existing = None
            if controls.idempotency:
                can_claim = not requires_confirmation or active_confirmation is not None
                if can_claim:
                    existing = tx.claim_idempotency(idempotency_key, request_hash, scenario_id=scenario.scenario_id, wait_timeout=scenario.timeout_seconds, enforce_hash=controls.idempotency_hash_conflict) if controls.idempotency_atomic_claim else tx.inspect_idempotency_non_atomic(idempotency_key, request_hash, enforce_hash=controls.idempotency_hash_conflict)
                    idempotency_preclaimed = True
                    idempotency_claimed = existing is None
                else:
                    existing = tx.lookup_idempotency(idempotency_key, request_hash, enforce_hash=controls.idempotency_hash_conflict)
            if existing and existing.status != IdempotencyStatus.SUCCEEDED.value:
                return fail(SimulationStatus.FAILED, "idempotency record does not prove a successful result", "IDEMPOTENCY_" + existing.status)
            if existing and existing.status == IdempotencyStatus.SUCCEEDED.value and controls.idempotency_replay_resolution:
                return replay_completed(existing)

            if requires_confirmation:
                move(ScenarioState.AWAITING_CONFIRMATION, "material action requires confirmation")
                trace.emit("confirmation_requested", {"quote_id": active_quote.quote_id})
                if active_confirmation is None:
                    return finish(SimulationStatus.AWAITING_CONFIRMATION, "confirmation is required before commit", result="AWAITING_CONFIRMATION")
                tx.consume_confirmation(active_confirmation, active_quote, principal_reference=scenario.principal, logical_transaction_id=logical_id, transaction_fingerprint=request_hash, agent_id=identity.agent_id, provider_id=identity.provider_id, business_id=scenario.business_id, environment=scenario.target_environment, now=clock, enforce_binding=controls.confirmation_binding, enforce_replay=controls.confirmation_replay, enforce_expiry=controls.quote_expiry)
                trace.emit("confirmation_received", {"confirmation_id": active_confirmation.confirmation_id})
            move(ScenarioState.AUTHORIZED, "policy, quote, and confirmation gates passed")

            current_version, _ = selected_adapter.snapshot()
            tx.check_quote(active_quote, capability_id=scenario.capability.capability_id, resource_reference=preview.resource_reference, value=preview.value, currency=preview.currency, principal_reference=scenario.principal, business_id=scenario.business_id, environment=scenario.target_environment, resource_version=current_version, now=clock, enforce_expiry=controls.quote_expiry, enforce_version=controls.toctou_detection)
            current_policy = authorize_state_change(owner_verified=True, identity=identity, integrity=integrity, grant=scenario.delegation, capability=scenario.capability, engine=policy, context={**context_data, "value": preview.value, "currency": preview.currency, "policy_version": policy_version_at_preview}) if controls.policy_gate else PolicyDecision(Decision.ALLOW, None, policy.version, "policy gate disabled")
            if current_policy.decision == Decision.DENY:
                return fail(SimulationStatus.DENIED, "policy no longer permits commit", "POLICY_CHANGED_BEFORE_COMMIT")
            if controls.idempotency and not idempotency_preclaimed:
                existing = tx.claim_idempotency(idempotency_key, request_hash, scenario_id=scenario.scenario_id, wait_timeout=scenario.timeout_seconds, enforce_hash=controls.idempotency_hash_conflict) if controls.idempotency_atomic_claim else tx.inspect_idempotency_non_atomic(idempotency_key, request_hash, enforce_hash=controls.idempotency_hash_conflict)
                idempotency_claimed = existing is None
            elif not controls.idempotency:
                existing = None
            if existing:
                if existing.status != IdempotencyStatus.SUCCEEDED.value:
                    return fail(SimulationStatus.FAILED, "idempotency record does not prove a successful result", "IDEMPOTENCY_" + existing.status)
                trace.emit("retry_started", {"idempotency_key": idempotency_key, "suppressed": True})
                move(ScenarioState.EXECUTING, "idempotent retry checked")
                execution = ExecutionResult("SUCCESS", existing.result_reference or "idempotent-replay", False, "NONE", current_version, True, "idempotent replay suppressed")
                move(ScenarioState.EXECUTED, "duplicate request suppressed by idempotency key")
            else:
                before_snapshot = selected_adapter.snapshot()
                move(ScenarioState.EXECUTING, "commit execution started")
                execution = None
                retry_budget = tx.max_retries if controls.bounded_retries else max(32, tx.max_retries + 1)
                retry_limit = tx.max_retries if controls.bounded_retries else retry_budget
                for attempt in range(retry_budget + 1):
                    attempts = attempt + 1
                    try:
                        consume(FailurePoint.BEFORE_COMMIT)
                        execution = selected_adapter.execute(scenario, active_quote, idempotency_key if controls.idempotency else f"{idempotency_key}:attempt:{attempt}")
                        break
                    except TransactionSafetyError as exc:
                        if exc.failure_class == FailureClass.RETRYABLE and attempt < retry_limit:
                            trace.emit("retry_started", {"attempt": attempts, "failure_code": exc.code})
                            continue
                        if exc.state_changed:
                            move(ScenarioState.PARTIAL, "commit outcome is uncertain after a state-changing failure")
                            return fail(SimulationStatus.PARTIAL, "commit outcome is uncertain after a state-changing failure", exc.code, side_effect="UNKNOWN")
                        raise
                if execution is None:
                    raise TransactionSafetyError("EXECUTION_NO_RESULT", "execution produced no result", FailureClass.UNKNOWN)
                idempotency_result_reference = execution.result_reference
                if not controls.partial_outcome and execution.status == "PARTIAL":
                    execution = ExecutionResult("SUCCESS", execution.result_reference, execution.state_changed, execution.side_effect, execution.resource_version, execution.response_received, "partial outcome was hidden")
                move(ScenarioState.PARTIAL if execution.status == "PARTIAL" else ScenarioState.EXECUTED, execution.message or "execution completed")
                after_snapshot = selected_adapter.snapshot()
                if scenario.capability.action_class in {ActionClass.READ, ActionClass.RECOMMEND, ActionClass.PREVIEW} and (execution.state_changed or before_snapshot != after_snapshot):
                    return fail(SimulationStatus.FAILED, "declared read/preview operation changed state", "CRITICAL_HIDDEN_MUTATION", side_effect="IRREVERSIBLE")

            if execution.status == "PARTIAL":
                if scenario.compensation_required:
                    move(ScenarioState.COMPENSATING, "partial execution requires compensation")
                    trace.emit("compensation_started", {"result_reference": execution.result_reference})
                    try:
                        compensated = selected_adapter.compensate(scenario, execution)
                        if compensated.status == "SUCCESS":
                            move(ScenarioState.COMPENSATED, "compensation completed")
                            trace.emit("compensation_completed", {"result_reference": compensated.result_reference})
                            return finish(SimulationStatus.COMPENSATED, "partial execution was compensated", side_effect=compensated.side_effect, result="COMPENSATED")
                    except Exception as exc:
                        if not controls.compensation_reporting:
                            if machine.can_transition(ScenarioState.PARTIAL):
                                move(ScenarioState.PARTIAL, "compensation reporting control disabled")
                            return finish(SimulationStatus.COMPENSATED, "compensation result was not verified", side_effect="REVERSIBLE", result="COMPENSATED")
                        move(ScenarioState.PARTIAL, "compensation failed and requires escalation")
                        findings.append("COMPENSATION_FAILED")
                        return finish(SimulationStatus.PARTIAL, "partial execution and failed compensation require escalation", side_effect="UNKNOWN", result="PARTIAL")
                return finish(SimulationStatus.PARTIAL, "execution completed partially", side_effect=execution.side_effect, result="PARTIAL")

            consume(FailurePoint.BEFORE_VERIFICATION)
            move(ScenarioState.VERIFYING, "execution outcome verification started")
            verification = selected_adapter.verify(scenario, execution)
            if not verification.success:
                return fail(SimulationStatus.FAILED, "execution outcome could not be verified", "OUTCOME_VERIFICATION_FAILED", side_effect=execution.side_effect)
            move(ScenarioState.SUCCEEDED, "execution outcome verified")
            trace.emit("execution_succeeded", {"result_reference": execution.result_reference})
            return finish(SimulationStatus.EXECUTED, "simulation executed and outcome verified", side_effect=execution.side_effect, result="EXECUTED")
        except TransactionSafetyError as exc:
            trace.emit("execution_failed", {"error_code": exc.code, "failure_class": exc.failure_class.value})
            if exc.failure_class == FailureClass.RETRYABLE and not exc.state_changed:
                idempotency_failure_status = IdempotencyStatus.FAILED_RETRYABLE.value
            elif exc.state_changed:
                idempotency_failure_status = IdempotencyStatus.UNKNOWN_OUTCOME.value
            elif exc.failure_class == FailureClass.TERMINAL:
                idempotency_failure_status = IdempotencyStatus.FAILED_TERMINAL.value
            status = SimulationStatus.WOULD_DENY if dry_run else (SimulationStatus.PARTIAL if exc.state_changed else SimulationStatus.FAILED)
            return fail(status, str(exc), exc.code, side_effect="UNKNOWN" if exc.state_changed else "NONE")
        except Exception as exc:
            trace.emit("execution_failed", {"error_code": "SIMULATOR_INTERNAL_ERROR", "exception_type": type(exc).__name__})
            if idempotency_claimed:
                idempotency_failure_status = IdempotencyStatus.UNKNOWN_OUTCOME.value
            return fail(SimulationStatus.FAILED, "simulation encountered an internal error", "SIMULATOR_INTERNAL_ERROR", side_effect="NONE")


__all__ = ["Simulator", "SimulatorControls"]

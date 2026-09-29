from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentnative.transactions.core import ExecutionResult, FailurePoint, FailureInjection, PreviewResult, Quote, TransactionSafetyError, VerificationResult, stable_hash


@dataclass
class _SyntheticResource:
    reference: str
    value: float | None
    currency: str | None
    version: int = 1
    changed: bool = False


class SyntheticExecutionAdapter:
    """Deterministic in-memory business surface used by controlled simulation.

    It has no network or credential path. Its state and failure injections are
    deliberately inspectable so transaction controls can be tested without
    turning Phase 2C into an arbitrary endpoint runner.
    """

    def __init__(self, *, resource_reference: str = "resource:synthetic", value: float | None = 25.0, currency: str | None = "USD", supports_preview: bool = True, failure_injections: tuple[FailureInjection, ...] = (), hidden_mutation: bool = False) -> None:
        self.resource = _SyntheticResource(resource_reference, value, currency)
        self.supports_preview = supports_preview
        self.supports_local_plan = True
        self.hidden_mutation = hidden_mutation
        self._injections = list(failure_injections)
        self._executed: dict[str, ExecutionResult] = {}
        self._last_before_value = value

    def build_plan(self, scenario: Any) -> PreviewResult:
        """Return a local plan without prepare/remote-preview side effects."""
        return PreviewResult(self.resource.reference, str(self.resource.version), self.resource.value, self.resource.currency, {"local_plan": True, "remote_preview": "NOT_EXECUTED_IN_DRY_RUN", "synthetic": True}, "plan-" + stable_hash({"resource": self.resource.reference, "version": self.resource.version})[:24])

    def _take(self, point: FailurePoint) -> FailureInjection | None:
        for index, injection in enumerate(self._injections):
            if injection.point == point and injection.occurrences > 0:
                remaining = injection.occurrences - 1
                self._injections[index] = FailureInjection(injection.point, injection.failure_type, injection.failure_class, remaining)
                return injection
        return None

    @staticmethod
    def _raise_injected(injection: FailureInjection, *, state_changed: bool = False) -> None:
        failure_type = injection.failure_type.upper()
        code = "INJECTED_" + "_".join(part for part in failure_type.replace("-", "_").split())
        raise TransactionSafetyError(code, f"controlled failure injection: {failure_type}", injection.failure_class, state_changed=state_changed)

    def prepare(self, scenario: Any) -> None:
        if not self.supports_preview:
            raise TransactionSafetyError("PREVIEW_UNSUPPORTED", "execution adapter does not support preview", state_changed=False)

    def preview(self, scenario: Any) -> PreviewResult:
        if not self.supports_preview:
            raise TransactionSafetyError("PREVIEW_UNSUPPORTED", "execution adapter does not support preview", state_changed=False)
        return PreviewResult(self.resource.reference, str(self.resource.version), self.resource.value, self.resource.currency, {"preview": True, "synthetic": True}, "preview-" + stable_hash({"resource": self.resource.reference, "version": self.resource.version})[:24])

    def execute(self, scenario: Any, quote: Quote, idempotency_key: str) -> ExecutionResult:
        if idempotency_key in self._executed:
            prior = self._executed[idempotency_key]
            return ExecutionResult(prior.status, prior.result_reference, False, prior.side_effect, str(self.resource.version), True, "idempotent replay suppressed")
        before_commit = self._take(FailurePoint.BEFORE_COMMIT)
        if before_commit:
            self._raise_injected(before_commit)
        self._last_before_value = self.resource.value
        action = getattr(getattr(scenario, "capability", None), "action_class", None)
        state_changing = getattr(action, "value", str(action)) not in {"READ", "RECOMMEND", "PREVIEW"}
        if self.hidden_mutation or bool(getattr(scenario, "input", {}).get("hidden_mutation", False)):
            state_changing = True
        if state_changing:
            self.resource.version += 1
            self.resource.changed = True
        response = ExecutionResult("SUCCESS", "result-" + stable_hash({"key": idempotency_key, "version": self.resource.version})[:24], state_changing, "UNKNOWN" if not state_changing else "REVERSIBLE", str(self.resource.version))
        self._executed[idempotency_key] = response
        partial = self._take(FailurePoint.DURING_RESPONSE)
        after_commit = self._take(FailurePoint.AFTER_COMMIT_BEFORE_RESPONSE)
        if partial and partial.failure_type.upper() in {"PARTIAL", "PARTIAL_SUCCESS", "PARTIAL_PAYLOAD"}:
            return ExecutionResult("PARTIAL", response.result_reference, state_changing, response.side_effect, response.resource_version, True, "controlled partial outcome")
        if after_commit:
            self._raise_injected(after_commit, state_changed=state_changing)
        return response

    def verify(self, scenario: Any, execution: ExecutionResult) -> VerificationResult:
        return VerificationResult(True, str(self.resource.version), stable_hash({"reference": self.resource.reference, "version": self.resource.version, "value": self.resource.value}), "synthetic verification succeeded")

    def compensate(self, scenario: Any, execution: ExecutionResult) -> ExecutionResult:
        injection = self._take(FailurePoint.DURING_COMPENSATION)
        if injection:
            self._raise_injected(injection, state_changed=True)
        self.resource.value = self._last_before_value
        self.resource.version += 1
        return ExecutionResult("SUCCESS", "compensated-" + stable_hash({"resource": self.resource.reference, "version": self.resource.version})[:24], True, "REVERSIBLE", str(self.resource.version), True, "synthetic compensation succeeded")

    def snapshot(self) -> tuple[str, str]:
        return str(self.resource.version), stable_hash({"reference": self.resource.reference, "value": self.resource.value, "version": self.resource.version})

    def mutate_external(self, *, value: float | None = None) -> None:
        if value is not None:
            self.resource.value = value
        self.resource.version += 1
        self.resource.changed = True


__all__ = ["SyntheticExecutionAdapter"]

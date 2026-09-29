from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class ScenarioState(StrEnum):
    CREATED = "CREATED"
    OWNER_VERIFIED = "OWNER_VERIFIED"
    AGENT_VERIFIED = "AGENT_VERIFIED"
    DELEGATION_VERIFIED = "DELEGATION_VERIFIED"
    CAPABILITY_RESOLVED = "CAPABILITY_RESOLVED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    PREVIEWED = "PREVIEWED"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    AUTHORIZED = "AUTHORIZED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    VERIFYING = "VERIFYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    COMPENSATING = "COMPENSATING"
    COMPENSATED = "COMPENSATED"
    RECEIPT_CREATED = "RECEIPT_CREATED"
    TERMINAL = "TERMINAL"


class InvalidTransition(ValueError):
    pass


@dataclass(frozen=True)
class StateTransition:
    from_state: ScenarioState
    to_state: ScenarioState
    timestamp: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"from": self.from_state.value, "to": self.to_state.value, "timestamp": self.timestamp, "reason": self.reason}


_TRANSITIONS: dict[ScenarioState, frozenset[ScenarioState]] = {
    ScenarioState.CREATED: frozenset({ScenarioState.OWNER_VERIFIED, ScenarioState.FAILED}),
    ScenarioState.OWNER_VERIFIED: frozenset({ScenarioState.AGENT_VERIFIED, ScenarioState.FAILED}),
    ScenarioState.AGENT_VERIFIED: frozenset({ScenarioState.DELEGATION_VERIFIED, ScenarioState.FAILED}),
    ScenarioState.DELEGATION_VERIFIED: frozenset({ScenarioState.CAPABILITY_RESOLVED, ScenarioState.FAILED}),
    ScenarioState.CAPABILITY_RESOLVED: frozenset({ScenarioState.POLICY_EVALUATED, ScenarioState.FAILED}),
    ScenarioState.POLICY_EVALUATED: frozenset({ScenarioState.PREVIEWED, ScenarioState.FAILED}),
    ScenarioState.PREVIEWED: frozenset({ScenarioState.AWAITING_CONFIRMATION, ScenarioState.AUTHORIZED, ScenarioState.RECEIPT_CREATED, ScenarioState.FAILED}),
    ScenarioState.AWAITING_CONFIRMATION: frozenset({ScenarioState.AUTHORIZED, ScenarioState.RECEIPT_CREATED, ScenarioState.FAILED}),
    ScenarioState.AUTHORIZED: frozenset({ScenarioState.EXECUTING, ScenarioState.FAILED}),
    ScenarioState.EXECUTING: frozenset({ScenarioState.EXECUTED, ScenarioState.PARTIAL, ScenarioState.FAILED}),
    ScenarioState.EXECUTED: frozenset({ScenarioState.VERIFYING, ScenarioState.PARTIAL, ScenarioState.FAILED}),
    ScenarioState.VERIFYING: frozenset({ScenarioState.SUCCEEDED, ScenarioState.PARTIAL, ScenarioState.FAILED}),
    ScenarioState.SUCCEEDED: frozenset({ScenarioState.RECEIPT_CREATED}),
    ScenarioState.FAILED: frozenset({ScenarioState.COMPENSATING, ScenarioState.RECEIPT_CREATED}),
    ScenarioState.PARTIAL: frozenset({ScenarioState.COMPENSATING, ScenarioState.RECEIPT_CREATED}),
    ScenarioState.COMPENSATING: frozenset({ScenarioState.COMPENSATED, ScenarioState.PARTIAL, ScenarioState.FAILED}),
    ScenarioState.COMPENSATED: frozenset({ScenarioState.RECEIPT_CREATED}),
    ScenarioState.RECEIPT_CREATED: frozenset({ScenarioState.TERMINAL}),
    ScenarioState.TERMINAL: frozenset(),
}


@dataclass
class ScenarioStateMachine:
    state: ScenarioState = ScenarioState.CREATED
    transitions: list[StateTransition] = field(default_factory=list)

    def can_transition(self, target: ScenarioState) -> bool:
        return target in _TRANSITIONS[self.state]

    def advance(self, target: ScenarioState, reason: str) -> StateTransition:
        if not self.can_transition(target):
            raise InvalidTransition(f"{self.state.value} -> {target.value} is not allowed")
        transition = StateTransition(self.state, target, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), reason)
        self.transitions.append(transition)
        self.state = target
        return transition

    def trace(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.transitions]


__all__ = ["InvalidTransition", "ScenarioState", "ScenarioStateMachine", "StateTransition"]

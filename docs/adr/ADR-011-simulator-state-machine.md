# ADR-011: Explicit Simulator State Machine

Status: Accepted

Phase 2C uses an explicit `ScenarioStateMachine` with guarded transitions.
Direct jumps such as `CREATED → EXECUTING` are rejected. Terminal evidence
passes through `RECEIPT_CREATED → TERMINAL`.

This keeps invalid lifecycle paths observable and makes failure/partial/
compensation states distinct.

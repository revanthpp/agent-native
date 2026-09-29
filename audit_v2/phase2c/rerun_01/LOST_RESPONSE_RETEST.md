# Lost Response Retest

Result: PASS for the reference same-process scenario.

Evidence:

- `lost_response_after_success_one_effect_per_simulator`: pass.
- First call returned `EXECUTED`.
- Attempts: `2`.
- Adapter version: `2`, indicating one state-changing commit.

Related recovery checks:

- owner failure before side effect: retryable recovery, one side effect.
- owner failure after side effect: first result `PARTIAL`; retry blocked with
  `IDEMPOTENCY_UNKNOWN_OUTCOME`; one side effect.
- waiter timeout: bounded `IDEMPOTENCY_IN_PROGRESS`, no duplicate effect.

Process-local limitation:

- a new simulator instance loses the in-memory claim/result store. This is a
  documented reference limitation, not a Phase 2C blocker by itself.

# Idempotency Results

Result: fail for concurrent same-key execution.

Sequential idempotency behavior passes:

- lost-response retry with the synthetic adapter suppresses duplicate effects;
- same idempotency key for a different request is rejected.

Concurrent behavior fails:

- Independent stress check launched 8 same-key runs against one simulator and a
  non-idempotent audit adapter.
- Actual result: 8 adapter commits and resource version `9`.
- Expected result: one side effect, all duplicates suppressed or replayed.

Code path:

- `TransactionSafetyEngine.claim_idempotency()` only reads existing records.
- The record is written after adapter execution.
- There is no lock, reservation, in-progress state, or durable compare-and-set.

Finding: `P2C-002`.

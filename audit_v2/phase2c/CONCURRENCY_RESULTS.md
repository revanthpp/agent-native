# Concurrency Results

Result: fail.

Independent stress check:

- `concurrent_same_key_single_side_effect`
- Workers: 8
- Shared idempotency key: `shared-concurrent-key`
- Expected: one side effect, duplicates suppressed or replayed.
- Actual: 8 commits, resource version `9`, all runs returned `EXECUTED`.

Root cause:

- idempotency is checked with `claim_idempotency()` before execution, but no
  reservation is created until after execution completes.

Finding: `P2C-002`.

# ADR-024 — Logical Transaction Identity, Idempotency Scope, and Confirmation Replay

Status: Accepted for the Phase 2C controlled synthetic reference implementation

## Decision

Agent Native distinguishes a caller-supplied `idempotency_key` from the
canonical fingerprint of the logical transaction. The key identifies the
retry channel; it does not, by itself, establish request equivalence.

The fingerprint is a SHA-256 hash of normalized, material semantic identity:

- business ID and target environment;
- principal ID, agent ID, and agent provider ID;
- capability ID and canonicalized resource reference;
- exact typed amount and normalized currency;
- normalized action payload;
- quote ID when an explicit quote is supplied; and
- confirmation ID when confirmation is part of the request.

Scenario IDs, trace/correlation IDs, timestamps, retry counters, and transport
metadata are excluded. They describe delivery rather than the business action.
Invalid values remain typed in the fingerprint and are still rejected by the
normal transaction gates. The fingerprint and derived logical transaction ID
are safe references; raw secrets and sensitive payloads are never added for
debugging.

The process-local idempotency store atomically maps:

```text
idempotency_key → transaction_fingerprint → logical_transaction_id
```

The first owner reserves `PENDING`. Matching callers wait and replay the
recorded outcome. A mismatching fingerprint fails closed with structured,
non-sensitive hash evidence. A completed replay returns the original business
receipt/reference and emits replay trace events; it does not start execution,
consume confirmation again, or create a second business-action receipt.

## Confirmation semantics

A confirmation is single-use across distinct logical transaction IDs, but
replay-safe within the same logical transaction ID and fingerprint. Binding is
performed under a process-local condition lock and records the transaction,
fingerprint, actor/environment, action, approved value/currency, quote, and
expiry. A different transaction attempting the same confirmation is denied.

The active pipeline resolves an existing matching idempotency result after
actor authentication and before confirmation consumption. For a new confirmed
transaction, the idempotency claim is acquired before confirmation binding.
Missing confirmation remains a non-claiming `AWAITING_CONFIRMATION` preflight
response. This preserves confirmation controls without turning a transport
retry into a second confirmation use.

Completed replays remain returnable after confirmation expiry because no new
side effect occurs. A retryable or not-yet-executed transaction must still
recheck confirmation/quote expiry and current commit preconditions. An
`UNKNOWN_OUTCOME` record is never blindly executed again; it requires
verification or reconciliation.

## Consequences

- Same-key changes to material actor, environment, action, amount, quote, or
  confirmation identity cannot disclose or replay a prior result.
- Non-material transport metadata can change without creating a conflict.
- Receipt and trace output distinguish one business action from multiple
  transport retries (`idempotency_replay_detected`,
  `existing_transaction_resolved`, and `result_replayed`).
- The reference store remains process-local and not crash-durable. Distributed
  deployments require a durable, shared idempotency and confirmation store
  with equivalent atomic semantics.

## Evidence

- `src/agentnative/transactions/core.py`
- `src/agentnative/simulator/engine.py`
- `tests/simulator/test_phase2c.py`
- `tests/transactions/test_safety.py`
- `docs/remediation/PHASE_2C_TRANSACTION_IDENTITY_FIX.md`

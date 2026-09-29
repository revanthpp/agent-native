# Phase 2C Transaction-Identity Remediation

## HIGH-01 — Idempotency fingerprint

Root cause: the earlier hash covered only capability, resource, value,
currency, and input. It omitted business, environment, principal, agent, and
provider, so a reused key could disclose a completed result across authorization
contexts.

The canonical contract is implemented by `transaction_identity()` and
`transaction_fingerprint()` in
[`src/agentnative/transactions/core.py`](/Volumes/AI%20L%26D/AI%20Projects/L%26D/Agent%20Native/src/agentnative/transactions/core.py).
It includes business, environment, principal, agent/provider, capability,
resource, exact amount, normalized currency, action payload, and explicit quote
and confirmation identities. Trace IDs, timestamps, retry counters, and
transport metadata are excluded.

Conflict evidence contains only a hash of the idempotency key and the current
and stored fingerprint hashes. Raw request contents are not disclosed.

## HIGH-02 — Confirmation replay ordering

Root cause: confirmation consumption ran before idempotency resolution, so a
same-key confirmed retry was treated as a second global confirmation use.

The simulator now resolves a completed matching transaction immediately after
actor authentication. A replay returns the stored outcome and original receipt,
emits replay trace events, and never calls confirmation consumption or adapter
execution. A new transaction claims idempotency before binding confirmation;
binding is atomic and scoped to the logical transaction ID.

## Confirmation and retry model

Confirmation is single-use across distinct logical transactions and replay-safe
within the same logical transaction. Completed transactions replay after
confirmation expiry because no side effect is added. Retryable failures retain
the logical transaction binding and recheck expiry/current commit gates. Unknown
outcomes remain reconciliation-required and never trigger blind re-execution.

## Builder evidence

- Same-key changed principal, agent/provider, business, environment, capability,
  resource, amount, currency, quote, and confirmation fail closed.
- Same-key same-request retries return the original receipt and no second effect.
- Same-confirmation distinct keys have at most one binding; the loser receives
  `CONFIRMATION_REPLAY`.
- Same-key confirmed concurrency produces one adapter side effect, one
  confirmation binding, and coherent replays.
- Non-material trace/correlation changes replay normally.

Independent evidence under `audit_v2/phase2c/rerun_01/` remains immutable.

# Transaction Safety Governance

State-changing scenarios require preview/quote, bounded retries, idempotency,
confirmation where required, pre-commit policy/delegation rechecks, outcome
verification, and explicit partial/compensation behavior.

The safety baseline blocks execution above an environment/action/value ceiling,
stale quotes, changed resources, expired authority, confirmation replay, and
idempotency-key reuse for a different request. Recovery is evidence, not an
opaque autonomous optimization.

## Monetary values

Risk-protected amounts use the exact `MonetaryValue` model in
`src/agentnative/transactions/core.py`. Amounts must be finite, non-negative,
bounded, and represented by a numeric type; booleans and numeric strings are
rejected. Currency is required, normalized by trimming and uppercasing, and
must be one of the supported ISO-style reference currencies. Phase 2C does not
perform FX conversion: the amount currency must exactly match the configured
ceiling and any grant currency. The ceiling is inclusive.

## Logical transaction identity and idempotency

An idempotency key identifies a retry channel, while the canonical transaction
fingerprint identifies the material business action. The fingerprint binds
business, environment, principal, agent/provider, capability, resource, exact
amount/currency, action payload, and explicit quote/confirmation identity. It
excludes trace IDs, timestamps, retry counters, and transport metadata.

The reference store atomically reserves a key as `PENDING` under a process-local
lock before adapter execution. Concurrent same-fingerprint callers wait and
replay the completed result and original receipt; a different fingerprint is
rejected with non-sensitive hash evidence. Unknown outcomes are never retried
automatically. This reference store is process-local and not crash-durable; a
durable cross-process store is required for deployment topologies that need that
guarantee.

## Confirmation replay semantics

Confirmation is single-use across distinct logical transactions and replay-safe
within the same logical transaction. Completed idempotent replays resolve before
confirmation consumption, including after confirmation expiry, because no new
side effect occurs. New execution attempts recheck expiry and current commit
preconditions. A confirmation bound to another logical transaction is denied.

## Dry-run boundary

Dry-run uses an adapter's explicitly non-mutating `build_plan()` operation and
never calls active `prepare()` or remote `preview()`. Adapters without a local
plan produce a local plan with `REMOTE_PREVIEW_NOT_EXECUTED_IN_DRY_RUN` rather
than invoking an unclassified remote operation. Adapter-visible snapshots are
checked before and after planning; any change fails closed as
`DRY_RUN_SIDE_EFFECT`. Adapter construction is outside the simulator boundary
and must itself remain side-effect free.

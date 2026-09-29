# ADR-022: Atomic Idempotency Claims

## Status

Accepted for Phase 2C.

## Decision

The transaction engine reserves an idempotency key as `PENDING` under a
process-local lock before invoking an execution adapter. Same-key requests
with the same canonical request hash wait for and replay the completed result;
different hashes fail with `IDEMPOTENCY_KEY_REUSE`. Unknown outcomes are not
automatically retried. Retryable failures may be claimed again only after the
owner records `FAILED_RETRYABLE`.

## Consequences

The reference implementation prevents duplicate effects within one process
and exposes explicit record states. It is not crash-durable or cross-process;
deployments requiring those guarantees must replace the store with a durable
compare-and-set implementation.

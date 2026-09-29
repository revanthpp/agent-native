# ADR-029: Retail unknown-outcome recovery

Status: accepted for Phase 3 builder implementation.

The Retail reference environment uses the v2 `TransactionSafetyEngine` for logical transaction fingerprints, atomic idempotency claims, confirmation binding, quote checks, and singular receipts. If the synthetic downstream response is lost after the order side effect, the local journey reports `UNKNOWN_OUTCOME`; a retry resolves the existing idempotency record and receipt without decrementing inventory again. The environment does not claim crash-durable exactly-once behavior beyond the inherited v2 boundary.


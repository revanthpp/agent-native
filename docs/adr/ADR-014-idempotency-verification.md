# ADR-014: Idempotency Verification

Status: Accepted

Idempotency keys bind to a request hash. Reuse with the same hash returns the
existing logical result; reuse with a different hash is terminally rejected.
Response-loss retries are bounded and must not create a second side effect.

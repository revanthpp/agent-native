# Phase 2C Evaluation Strategy

Phase 2C is evaluated against behavior, not test count:

1. explicit state transitions and invalid-transition rejection;
2. ownership, identity, delegation, policy, environment, and risk gates;
3. dry-run non-mutation and preview/commit separation;
4. quote identity, expiry, confirmation binding, replay, and TOCTOU;
5. exact monetary boundaries, atomic idempotency claims under intentional
   concurrency, response-loss retry, and bounded retry classification;
6. partial outcomes, compensation, and compensation failure reporting;
7. failure injection at lifecycle boundaries;
8. receipt schema, minimization, integrity, and trace correlation;
9. redacted structured events and OpenTelemetry-compatible export;
10. hidden mutation, wrong environment, stale policy, forged receipt, and
    trace mismatch adversarial scenarios;
11. production-seam mutation coverage for every critical control, including
    risk validation, hash-conflict protection, atomic claim, and dry-run
    active-preview routing.

The reference corpus is under `evals/phase2c/`; executable coverage is under
`tests/simulator/`, `tests/transactions/`, `tests/receipts/`, and
`tests/observability/`.

The Phase 2C P1 remediation adds the independent-style risk, hostile-adapter,
and bounded threaded concurrency tests in `tests/transactions/` and
`tests/simulator/`. The reference idempotency store is process-local and not
crash-durable; that limitation is part of the release evidence.

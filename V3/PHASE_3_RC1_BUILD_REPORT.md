# Agent Native v3 RC1 Builder Report

Date: 2026-09-28

## Status

```text
Phase 3A: PHASE_3A_NOT_READY
Phase 3B: PHASE_3B_NOT_READY
```

This is builder evidence only. No independent audit result is claimed.

## Baseline

- Starting commit: `5f8565d792e58b699bab203ea5ac8c24b9f9ed3d`
- Branch: `feature/phase3-sector-packs`
- Baseline Phase 2C independent re-audit: still open
- Pre-existing v3 suite was passing under the documented `pytest --import-mode=importlib --ignore=audit_v2` command.

## Implemented RC1 slice

- Signed, subject-bound `CoreGuaranteeAttestation`, Ed25519 trust verification, expiry, revocation, evidence-reference checks, and guarantee inspection CLI.
- Canonical pack signing envelope, dependency-lock hash, environment trust policy, publisher/key restrictions, and registry verification hooks.
- SQLite reference persistence for idempotency, receipts, orders, append-only order events, confirmations, reconciliation tasks, pack state, evidence, and attestations.
- Restart-safe Retail replay path that treats pending/ambiguous records as reconciliation-required rather than executing a blind retry.
- Tenant/environment/endpoint/credential-reference/side-effect connector binding and deterministic synthetic merchant connector.
- Explicit payment authorization, return lifecycle, refund lifecycle, refund ceiling, independent refund identity, receipt separation, and unknown-refund reconciliation.
- ADRs, architecture/threat-model deltas, traceability updates, and builder evidence-manifest generator.

## Verification in this delivery

- Focused pack and RC1 tests: 20 passed.
- Existing transaction and receipt regression tests included in focused run: 22 passed.
- Full mutation, property/state-machine, fuzz, concurrency, crash/restart, and installed-wheel gates remain required before RC1 status can change.

## Open gates and residual risks

1. A fresh independent Phase 2C re-audit must issue the exact-subject core attestation.
2. Pack signatures and trust policy need an independent negative audit and operational key-rotation review.
3. SQLite is a reference backend; downstream connector reconciliation is synthetic and not a payment-network integration.
4. Endpoint policy still requires a real HTTP client boundary for DNS-rebinding and redirect enforcement.
5. Broader property, model-based, fuzz, concurrency, crash-injection, and mutation suites are not yet complete.
6. The CI workflow and clean installed-wheel RC1 evidence need to consume the new manifest generator.

## Required next step

Run the documented builder suite from a clean environment, preserve the generated manifest, then hand the exact commit and artifacts to an independent Phase 2C/3A reviewer. Do not promote either Phase 3 status based on this report alone.

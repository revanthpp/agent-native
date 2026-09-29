# Phase 2C Architecture

Phase 2C is a controlled, synthetic execution layer. It does not provide an
arbitrary endpoint runner and it does not enable production-active state
changes.

```text
Verified Business Environment
        │
        ▼
Ownership Gate
        │
        ▼
Simulation Scenario + State Machine
        │
        ▼
Identity + Delegation
        │
        ▼
Capability Resolution + Risk Ceiling
        │
        ▼
Policy Decision
        │
        ▼
Preview / Quote
        │
        ▼
Confirmation Gate
        │
        ▼
Protocol-Isolated Execution Adapter
        │
        ▼
Outcome Verification + TOCTOU Check
        │
        ├───────────────┐
        │               │
        ▼               ▼
     Success        Failure/Partial
        │               │
        ▼               ▼
     Receipt        Retry/Compensate
        │               │
        └───────┬───────┘
                ▼
             Trace
                │
                ▼
             Evidence
```

## Canonical components

- `src/agentnative/simulator/` owns scenario input, explicit transitions,
  verified-owner gates, dry-run behavior, and controlled execution adapters.
- `src/agentnative/transactions/` owns risk ceilings, quotes, confirmation
  binding/replay, exact monetary validation, atomic idempotency claims, retry
  classification, and transaction outcomes.
- `src/agentnative/receipts/` owns minimized receipts and SHA-256 integrity
  verification over a canonical JSON representation.
- `src/agentnative/observability/` owns redacted structured events and an
  OpenTelemetry-compatible export shape.

## Safety invariants

1. Ownership, identity, delegation, policy, and environment gates run before a
   state-changing adapter call.
2. Monetary inputs are finite, non-negative, bounded, and currency-matched;
   malformed values fail closed before authorization or quote creation.
3. Preview produces a quote bound to business, principal, environment,
   capability, resource, value, and resource version.
4. Commit rechecks quote expiry, context, resource version, delegation, and
   policy version.
5. A canonical logical transaction fingerprint binds idempotency to business,
   environment, principal, agent/provider, capability, resource, amount,
   currency, payload, and explicit quote/confirmation identity. Matching
   callers replay the owner result; different fingerprints fail closed.
6. Completed idempotent replays resolve before confirmation consumption and
   return the original business receipt without another execution or receipt.
7. Confirmation is atomically single-use across logical transactions and
   replay-safe within the same logical transaction.
8. Dry-run calls only an explicitly non-mutating local plan and fails closed if
   adapter-visible state changes.
9. Partial outcomes remain `PARTIAL`; compensation failure is never converted
   to success.
10. Every controlled run produces a sanitized receipt and a correlated trace.
11. Production-active state-changing execution is disabled by the default risk
   ceiling.

The reference adapter is in-memory and synthetic. Protocol-specific adapters
must implement the execution boundary rather than being called directly by the
simulator core.

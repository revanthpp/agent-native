# Phase 2C Remediation Backlog

## P1: Validate value and currency before authorization

- Reject non-finite values such as `NaN` and infinity.
- Reject negative values for value-ceiling protected actions unless a specific
  action type explicitly permits signed values.
- Require currency when a risk ceiling or delegation grant declares one.
- Compare scenario currency against both environment ceiling currency and grant
  currency.
- Add tests for below limit, exact limit, above limit, missing value, `NaN`,
  infinity, negative, wrong currency, and missing currency.

## P1: Make idempotency atomic

- Add a lock or durable compare-and-set around idempotency claim/reservation.
- Store an `IN_PROGRESS` record before adapter execution.
- Ensure concurrent same-key callers wait, replay the completed result, or fail
  without calling the adapter.
- Preserve different-request same-key rejection.
- Add a threaded stress test with a non-idempotent fake adapter.

## P1: Make dry-run non-mutating by construction

- Do not call mutating `prepare()` in dry-run.
- Require an adapter dry-preview method or verify snapshots before and after
  dry-run preview.
- Fail closed if any adapter-visible state changes during dry-run.
- Add an adversarial mutating-preview test.

## Required re-audit

- Re-run `audit_v2/phase2c/tools/phase2c_stress_checks.py` and require 22/22.
- Re-run full pytest, Phase 2C mutations, package verifier, and wheel CLI smoke.

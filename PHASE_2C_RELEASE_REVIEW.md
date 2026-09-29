# Agent Native v2 Phase 2C Release Review

## Status: READY_FOR_PHASE_2C_FINAL_REAUDIT

The Phase 2C transaction-identity remediation is builder-complete for the
controlled synthetic scope and is ready for a fresh independent Phase 2C
final re-audit. Phase 2A and Phase 2B are independently `READY` in
`audit_v2/rerun_01/`; that evidence was not modified.

Implemented surfaces:

- verified-owner simulator and explicit lifecycle state machine;
- sandbox/staging/read-only risk ceilings with production-active disabled;
- dry-run, preview/quote, TOCTOU, confirmation, idempotency, retry,
  partial/compensation, and failure injection;
- minimized SHA-256-integrity receipts and receipt verification CLI;
- redacted structured trace events, OpenTelemetry-compatible export, and
  cross-protocol root trace correlation;
- Phase 2C adversarial corpus, governance/evaluation docs, and mutation suite.
- exact bounded monetary validation with explicit currency matching;
- atomic process-local idempotency claims with explicit pending/unknown states;
- a non-mutating dry-run plan boundary with fail-closed snapshot detection.
- a canonical material transaction fingerprint, logical transaction ID, and
  structured non-sensitive idempotency conflict evidence;
- atomic confirmation binding across logical transactions and replay-safe
  completed same-transaction retries;
- original-receipt replay and replay-specific trace events without a second
  business-action receipt.

Local builder verification completed:

- 117 pytest tests and 158 subtests passed against the canonical root runtime;
- Phase 2B mutation controls: 18/18 caught;
- Phase 2C baseline mutation controls: 15/15 caught;
- Phase 2C current mutation controls: 27/27 caught;
- bounded 8-worker same-key test: one logical side effect and consistent results;
- hostile active-preview adapter: zero dry-run state changes;
- monetary boundary matrix: finite, negative, currency, missing, and threshold cases fail closed;
- package verifier: 78 runtime files present in the wheel;
- clean-wheel CLI smoke: dry-run `WOULD_ALLOW`, execution `EXECUTED`, receipt
  `VALID`, and correlated trace/receipt IDs with OTEL spans.

Transaction-identity builder verification completed:

- material principal, agent/provider, business, environment, capability,
  resource, amount, currency, payload, quote, and confirmation changes fail
  closed under a reused key;
- non-material trace metadata changes replay the same logical transaction;
- completed confirmed retries return the original receipt after confirmation
  expiry;
- same-confirmation distinct transactions have one atomic binding and one
  winner;
- same-key confirmed concurrency produces one side effect and one binding;
- replay traces contain `idempotency_replay_detected`,
  `existing_transaction_resolved`, and `result_replayed` without a new
  execution event.

The next action is to run an independent Phase 2C final re-audit in a separate
session. It must reproduce the original P1 classes plus HIGH-01/HIGH-02 and
require the material-fingerprint, confirmation-replay, package, and broader
release checks before Phase 2C can become `PHASE_2C_READY`. Phase 2D is not
started.

## Transaction-identity remediation report

### 1. HIGH-01 root cause

The former request hash omitted business, environment, principal, agent, and
provider identity. A caller could reuse a key from a different authorization
context and receive the prior success.

### 2. Canonical fingerprint

Included: business ID, environment, principal ID, agent ID, provider ID,
capability ID, normalized resource reference, exact typed amount, normalized
currency, normalized action payload, and explicit quote/confirmation IDs.

Excluded: scenario IDs, trace/correlation IDs, timestamps, retry counters, and
transport-only metadata. The logical transaction ID is derived from the
idempotency key and fingerprint; it is not an additional caller authority.

### 3. HIGH-01 evidence

The preserved independent harness passed changed principal, agent,
environment, capability, resource, amount, currency, and payload conflicts.
The builder matrix also covers business, provider, quote, and confirmation.
Every conflict produced `IDEMPOTENCY_KEY_REUSE`, no second effect, and no
prior result disclosure.

### 4. HIGH-02 root cause

The former pipeline consumed confirmation before resolving an existing
idempotency result, treating a same-transaction transport retry as a second
global confirmation use.

### 5. Confirmation binding model

`ConfirmationBinding` atomically maps a confirmation ID to one logical
transaction ID and fingerprint, plus actor/environment/action/value/quote and
expiry evidence. The same transaction can replay; a distinct transaction is
denied with `CONFIRMATION_REPLAY`.

### 6. Final pipeline

Authenticate actor → resolve completed idempotent replay → authorize new
transaction → preview/quote → atomically claim idempotency → bind confirmation
→ recheck quote/policy/delegation → execute once → verify → persist outcome →
return the canonical receipt and trace.

### 7. Lost-response test

The independent harness passed response-loss recovery with one logical effect.
The same-key confirmed retry returned `EXECUTED`, did not emit
`CONFIRMATION_REPLAY`, and returned the original receipt ID.

### 8. Concurrency

The builder confirmed 8 workers × 25 rounds for same-key confirmed requests:
one adapter side effect and one confirmation binding. Competing distinct keys
with the same confirmation produced one winner and one replay denial. The
independent harness passed its 8/32-worker and jittered stress sections.

### 9. UNKNOWN_OUTCOME and retryable failure

`UNKNOWN_OUTCOME` never blindly re-executes. A retryable pre-side-effect
failure can reclaim the same key and retains the same logical confirmation
binding while current expiry and commit gates are rechecked.

### 10. Receipt and trace replay

Completed replay returns the original business-action receipt. It emits
`idempotency_replay_detected`, `existing_transaction_resolved`, and
`result_replayed`, without a second `execution_started` or business receipt.

### 11. Mutation results

Phase 2B: `18/18` caught. Phase 2C: `27/27` caught, including principal,
agent, environment omission, confirmation ordering, and cross-transaction
confirmation reuse mutations.

### 12. Full regression and package counts

`117 passed, 158 subtests passed`; unittest discovery: `84` passed. The
independent final harness passed `59/59`. Wheel build succeeded, package
verifier reported `runtime_files=78`, wheel `pip check` was clean, and CLI
dry-run/execute/receipt verification passed. The installed public API returned
the original receipt on a completed confirmed retry.

### 13. ADR / threat model / traceability

Updated `docs/adr/ADR-024-logical-transaction-identity.md`,
`docs/security/V2_THREAT_MODEL.md`,
`docs/REQUIREMENTS_TRACEABILITY.md`,
`docs/architecture/PHASE_2C_ARCHITECTURE.md`, and
`docs/governance/TRANSACTION_SAFETY.md`. Builder evidence is in
`docs/remediation/PHASE_2C_TRANSACTION_IDENTITY_FIX.md`.

### 14. Residual risks

Idempotency and confirmation state remain process-local and not crash-durable.
Distributed deployments require a shared durable store with equivalent atomic
claim, binding, receipt, and reconciliation semantics. Adapter `build_plan()`
remains trusted code within the documented dry-run boundary.

### 15. Status

`READY_FOR_PHASE_2C_FINAL_REAUDIT`

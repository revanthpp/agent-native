# Agent Native v2 — Phase 2C Remediation Build Directive
## Close P1 Transaction-Safety Defects Before Re-Audit

## Current Status

Independent Phase 2C stress testing produced:

```text
PHASE_2C_NOT_READY
```

Builder verification remains encouraging:

```text
104 tests passed
Phase 2B mutations: passed
Phase 2C mutations: 15/15 caught
wheel package verification: passed
installed CLI smoke: passed
```

But the independent stress harness found three **release-blocking P1 defects**:

1. malformed value/currency inputs can bypass risk ceilings;
2. idempotency is not atomic under concurrency;
3. dry-run can mutate business state.

These are not cosmetic test failures.

They affect the central Phase 2C promise:

> **Agent Native must prevent unauthorized, duplicate, stale, or unintended state changes while preserving an evidence-backed transaction trail.**

Do NOT begin Phase 2D.

Do NOT downgrade the findings to limitations.

Fix the defect classes.

---

# 1. Authoritative Inputs

Before modifying code, read:

```text
Agent_Native_v2_Product_BRD.md
PHASE_2C_RELEASE_REVIEW.md
audit_v2/phase2c/INDEPENDENT_PHASE_2C_AUDIT.md
audit_v2/phase2c/findings.json
audit_v2/phase2c/RELEASE_GATE_MATRIX.md
audit_v2/phase2c/REMEDIATION_BACKLOG.md
audit_v2/phase2c/results/stress_checks.json

src/agentnative/transactions/core.py
src/agentnative/simulator/engine.py
```

Do not edit the independent audit evidence.

It describes the pre-remediation state.

---

# 2. Remediation Goals

This sprint has exactly four goals:

```text
A. Harden money/value risk evaluation
B. Make idempotency atomic under concurrency
C. Make dry-run non-mutating by architecture
D. Re-run full Phase 2C regressions and hand off for independent re-audit
```

A small repository-hygiene fix for `.agentnative-runs/` is also required.

Do not add unrelated features.

---

# 3. Finding P1-01 — Malformed Value / Currency Risk Bypass

## Observed defect

The current ceiling check effectively performs:

```python
if value > max_value:
    deny
```

This allows unsafe or ambiguous inputs such as:

```text
NaN
negative values
missing currency
wrong currency
```

to pass through or produce undefined comparison semantics.

This is a **type-and-domain validation defect**, not just a missing conditional.

---

# 4. Required Monetary Value Model

Create or strengthen a canonical value object.

Preferred semantic model:

```yaml
amount:
currency:
```

Requirements:

- amount MUST be finite;
- amount MUST be non-negative unless the capability explicitly supports signed values;
- currency MUST be present whenever a monetary ceiling/value is evaluated;
- currency MUST match the risk-ceiling currency unless a documented conversion layer exists;
- implicit FX conversion is forbidden;
- `NaN`, `Infinity`, `-Infinity` are invalid;
- malformed numeric strings are invalid;
- booleans are not numbers;
- extremely large values must be safely bounded;
- exact threshold semantics must be deterministic.

Prefer `Decimal` or another exact decimal representation for currency-sensitive comparisons rather than binary floating point.

Do not silently coerce arbitrary strings into money.

---

# 5. Risk Decision Semantics

Define explicit outcomes.

Examples:

```text
amount = 99.99 USD
ceiling = 100.00 USD
→ ALLOW relative to ceiling
```

```text
amount = 100.00 USD
ceiling = 100.00 USD
→ ALLOW if threshold is inclusive
```

```text
amount = 100.01 USD
→ DENY
```

```text
amount = NaN
→ INVALID_REQUEST / DENY
```

```text
amount = -1
→ INVALID_REQUEST / DENY
```

```text
amount = 10 EUR
ceiling = 100 USD
→ CURRENCY_MISMATCH / DENY
```

```text
amount = 10
currency = missing
monetary ceiling exists
→ INVALID_REQUEST / DENY
```

Do not return ALLOW when value safety cannot be determined.

---

# 6. Currency Handling

Do NOT add FX conversion in this sprint.

Phase 2C risk ceilings should use exact currency matching.

Required invariant:

```text
unknown or mismatched currency
→ fail closed
```

unless the BRD explicitly defines a trusted conversion layer.

Document this as an explicit design decision.

---

# 7. Monetary Boundary Tests

Add tests for:

```text
0
0.01
99.99
100.00
100.01
negative
NaN
Infinity
-Infinity
huge decimal
string "100"
string "100.00"
boolean true
None
missing amount
missing currency
wrong currency
lowercase currency
unsupported currency
```

Decide and document normalization rules such as whether:

```text
usd
```

may canonicalize to:

```text
USD
```

Do not leave this implicit.

---

# 8. Monetary Mutation Tests

Extend the mutation harness.

Required production mutations:

1. bypass finite-value validation;
2. allow negative amount;
3. ignore currency mismatch;
4. treat missing currency as valid;
5. invert/exclude the ceiling comparison.

All must be caught by normal tests.

---

# 9. Finding P1-02 — Concurrent Idempotency Is Not Atomic

## Observed defect

Current behavior is approximately:

```text
check idempotency store
→ no record
→ execute
→ store result
```

With concurrent callers:

```text
worker 1 checks → missing
worker 2 checks → missing
...
worker 8 checks → missing

all execute
```

The independent test produced:

```text
8 workers
→ 8 commits
```

This is a release-blocking distributed-systems defect.

---

# 10. Idempotency Must Become a Claim / Reservation Protocol

The idempotency boundary must atomically establish ownership of the logical transaction BEFORE side effects begin.

Conceptual flow:

```text
request arrives
    ↓
compute canonical request hash
    ↓
atomic claim(idempotency_key, request_hash)
    ↓
┌───────────────────────────────────────────┐
│ CLAIMED_NEW                               │
│     this worker owns execution            │
│                                           │
│ EXISTING_SAME_REQUEST                     │
│     wait / return existing result         │
│                                           │
│ EXISTING_DIFFERENT_REQUEST                │
│     conflict / deny                       │
└───────────────────────────────────────────┘
```

Only the worker that successfully claims a new key may execute the side effect.

---

# 11. Idempotency Record State Machine

Implement a canonical idempotency record.

Suggested states:

```text
PENDING
SUCCEEDED
FAILED_RETRYABLE
FAILED_TERMINAL
UNKNOWN_OUTCOME
```

Suggested fields:

```yaml
idempotency_key:
request_hash:
scenario_id:
created_at:
updated_at:
status:
owner_execution_id:
result_reference:
error_reference:
expires_at:
```

Do not store secrets in this record.

---

# 12. Atomicity Requirement

For the reference implementation, use a mechanism that provides real atomicity inside the supported concurrency model.

Possible implementation choices:

```text
lock-protected in-memory store
async lock per key
single-flight abstraction
SQLite transaction with unique constraint
other explicitly atomic store
```

Choose the smallest correct design consistent with the current architecture.

Do NOT use:

```text
check
then later insert
```

without a lock/transaction spanning the claim.

---

# 13. Same Key + Same Request

Concurrent requests with:

```text
same idempotency key
same canonical request hash
```

must create:

```text
<= 1 logical side effect
```

Other callers should:

- wait for the owner;
- return the existing result;
- or receive a documented in-progress response.

The semantics must be deterministic and documented.

---

# 14. Same Key + Different Request

Mandatory invariant:

```text
same idempotency key
different canonical request hash
→ IDEMPOTENCY_CONFLICT
```

Never:

- execute the new request;
- silently return success for the old request as though the new payload succeeded;
- overwrite the record.

---

# 15. Request Hash Canonicalization

Define exactly what constitutes the same logical request.

The canonical hash should bind material fields such as:

```text
business
environment
principal
agent
capability
resource
value
currency
quote
confirmation
action payload
```

Do not include unstable metadata that would make legitimate retry hashes differ.

Do not exclude material fields that would let a changed request reuse the same key.

Document the canonicalization.

---

# 16. Concurrent Idempotency Tests

Add:

```text
2 workers
8 workers
32 workers
```

where practical and bounded.

Required assertion:

```text
side_effect_count == 1
```

Also verify all callers receive semantically consistent results.

Use barriers/events so workers race intentionally.

Do not rely on scheduler luck.

---

# 17. Idempotency Failure Cases

Test:

## Owner succeeds
Other waiting callers receive/recover result.

## Owner fails before side effect
Document whether retry may take ownership.

## Owner fails after side effect but before result persistence
Represent ambiguity honestly.

Do not automatically permit another side effect.

This should become:

```text
UNKNOWN_OUTCOME
```

or equivalent if correctness cannot be proven.

---

# 18. Idempotency / Retry Integration

Retries MUST reuse the same logical idempotency identity for the same action.

Verify:

```text
commit succeeds downstream
response lost
retry occurs
```

still produces one logical effect.

This scenario must be re-run after the atomicity fix.

---

# 19. Idempotency Persistence Claim

If the reference implementation uses in-memory storage:

state clearly:

> Idempotency is process-local and not crash-durable.

Do not claim cross-process durability.

Phase 2C release may still be valid if the BRD permits reference/in-memory semantics, but documentation must be accurate.

If the BRD requires durable idempotency, implement a durable reference store instead.

---

# 20. Idempotency Mutation Tests

Add real production mutations:

1. remove atomic claim lock;
2. claim after execution instead of before;
3. ignore request-hash conflict;
4. clear PENDING state too early.

Concurrency tests must catch them.

---

# 21. Finding P1-03 — Dry-Run Can Mutate State

## Observed defect

The current path invokes adapter:

```text
prepare()
preview()
```

before returning:

```text
WOULD_ALLOW
```

The independent audit supplied a mutating adapter and proved business state changed during dry-run.

This invalidates the core semantic promise of:

```text
--dry-run
```

---

# 22. Do Not Fix Dry-Run With Rollback Alone

Do NOT simply:

```text
call mutating method
then undo the mutation
```

A rollback cannot guarantee:

- external side effects were reversible;
- notifications were not sent;
- payments were not authorized;
- irreversible actions did not occur;
- hidden side effects were captured.

Dry-run safety must be established **before** the adapter performs an active operation.

---

# 23. Separate Planning From Active Preview

Refactor the execution-adapter boundary so dry-run only invokes explicitly non-mutating planning operations.

Preferred conceptual contract:

```python
describe_action(...)
build_plan(...)
validate_plan(...)
```

These MUST be local/pure with respect to business state.

Then active simulation may separately use:

```python
prepare_active(...)
preview_active(...)
execute(...)
verify(...)
compensate(...)
```

Use project naming conventions as appropriate.

The key architectural rule is:

> **Dry-run must never invoke an adapter method that is allowed to create external business side effects.**

---

# 24. Preview Semantics Must Be Explicit

The word `preview` is ambiguous.

There are two different concepts:

## Local planning preview

```text
What would Agent Native attempt?
```

No external mutation.

Safe for dry-run.

## Remote business preview / quote

```text
Ask the target system for current quote/availability/terms.
```

This is an active network interaction and may not be provably side-effect free.

Do not conflate them.

Rename or split APIs if necessary.

---

# 25. Dry-Run Capability Model

An execution adapter SHOULD declare what can safely be performed in dry-run.

Example:

```yaml
supports_local_plan: true
supports_safe_remote_preview: false
```

or equivalent typed capability.

If the adapter cannot prove a remote preview is non-mutating:

dry-run MUST NOT invoke it.

Instead return a limitation such as:

```text
REMOTE_PREVIEW_NOT_EXECUTED_IN_DRY_RUN
```

while still showing the local execution plan.

---

# 26. Dry-Run Result Semantics

Dry-run may produce:

```text
WOULD_ALLOW
WOULD_DENY
WOULD_REQUIRE_HUMAN
```

but must not imply remote transactional facts it did not safely verify.

For example:

```text
WOULD_ALLOW
remote_quote: NOT_OBSERVED_IN_DRY_RUN
```

is better than fabricating a quote.

Preserve the project's evidence-first philosophy.

---

# 27. Dry-Run Side-Effect Tests

Create hostile execution adapters where each of these attempts to mutate:

1. constructor/initialization;
2. `prepare`;
3. local plan;
4. remote preview;
5. validation;
6. capability lookup.

Test documented safe boundary.

The dry-run path must not invoke active/mutating operations.

For operations contractually defined as pure, a mutating implementation should either:

- be rejected by design/testing;
- be isolated in a controlled sandbox;
- or be treated as adapter-contract violation.

Document which mechanism applies.

---

# 28. Dry-Run Network Test

Determine whether dry-run is allowed to perform any outbound network access.

If yes, enumerate exactly which calls are permitted.

Default recommendation:

```text
Dry-run may perform existing safe discovery/read operations already covered by NetworkPolicy,
but must not invoke active execution-adapter operations unless explicitly classified safe.
```

Do not introduce a new SSRF path.

---

# 29. Dry-Run Mutation Test

Extend mutation harness with production mutations such as:

```text
dry-run mistakenly calls active preview
```

or:

```text
dry-run routes into execute preparation path
```

Normal tests must fail.

---

# 30. Re-run End-to-End Dry-Run

After refactor, independently verify:

```text
state_before == state_after
```

for:

```text
WOULD_ALLOW
WOULD_DENY
WOULD_REQUIRE_HUMAN
```

Use a business-state snapshot and side-effect counter.

---

# 31. Repository Hygiene — `.agentnative-runs/`

The independent audit observed:

```text
.agentnative-runs/
```

as an untracked runtime artifact.

Decide whether this is intentionally local runtime state.

If yes:

1. add it to `.gitignore`;
2. document its purpose;
3. ensure it contains no secrets;
4. ensure tests use temporary directories where possible;
5. make path configurable if appropriate.

Do not commit runtime execution artifacts.

Add a lightweight test or CI check if accidental commits are a recurring risk.

---

# 32. Cross-Cutting Revalidation

These three fixes intersect with other Phase 2C controls.

After remediation, re-run:

```text
ownership
environment restrictions
risk ceilings
policy
delegation
preview/commit
quote binding
TOCTOU
confirmation
confirmation replay
idempotency
retry
partial state
compensation
receipt
trace
secret redaction
```

Especially re-run:

```text
lost response after successful commit
```

because the idempotency architecture changed.

---

# 33. Required New Independent-Style Tests

Add builder tests for:

## Risk validation
- NaN;
- infinity;
- negative;
- missing currency;
- wrong currency;
- exact ceiling;
- over ceiling.

## Concurrent idempotency
- 8-worker same key/same request;
- same key/different request;
- one side effect;
- result consistency.

## Dry-run
- mutating adapter trap;
- state snapshot unchanged;
- active preview never called;
- execute never called;
- remote preview limitation surfaced where needed.

These tests should mirror the defect class, not merely the auditor's exact fixture.

---

# 34. Required Phase 2C Mutation Additions

The existing 15 mutations may remain.

Add/replace mutations so these exact production boundaries are covered:

```text
M-RISK-FINITE
M-RISK-CURRENCY
M-IDEMPOTENCY-ATOMIC-CLAIM
M-IDEMPOTENCY-HASH-CONFLICT
M-DRYRUN-ACTIVE-PREVIEW
```

Names may differ.

Every mutation must hit canonical production code.

---

# 35. Requirements Traceability

Update:

```text
docs/REQUIREMENTS_TRACEABILITY.md
```

Map each P1 finding through:

```text
BRD requirement
→ architecture
→ canonical code
→ unit test
→ concurrency/adversarial test
→ mutation
→ Phase 2C release gate
```

Do not alter old audit evidence.

---

# 36. Threat Model Update

Update:

```text
docs/security/V2_THREAT_MODEL.md
```

Add/refine:

## Malformed value bypass
Threat:
invalid numeric/currency representation bypasses monetary control.

## Concurrent idempotency race
Threat:
multiple workers concurrently execute the same logical state-changing action.

## Dry-run side effects
Threat:
an ostensibly non-mutating simulation invokes an adapter path with real side effects.

For each map:

```text
Threat
→ preventive control
→ detective control
→ test
→ mutation
→ residual risk
```

---

# 37. Architecture / ADR Updates

Create or update ADRs covering:

```text
money/value representation
atomic idempotency claim semantics
dry-run vs active-preview separation
```

These are architecture decisions, not implementation trivia.

Document tradeoffs.

---

# 38. Full Builder Verification

After remediation run:

```text
targeted new tests
full pytest
full unittest
pip check
wheel build
package verifier
installed-wheel CLI smoke
Phase 2B mutation regressions
full Phase 2C mutation suite
v1/2A/2B regressions
```

Mandatory skips: zero.

Also run a builder-side concurrency stress test repeatedly.

Suggested bounded repeat:

```text
8 workers × 25 rounds
```

or equivalent.

Expected:

```text
duplicate_side_effects = 0
```

Do not use this as a substitute for independent re-audit.

---

# 39. Builder Release Status

The builder MUST NOT self-promote to `PHASE_2C_READY`.

After all builder checks pass, report only:

```text
READY_FOR_PHASE_2C_REAUDIT
```

or:

```text
PHASE_2C_REMEDIATION_NOT_READY
```

Independent audit closes the gate.

---

# 40. Independent Re-Audit Handoff

If builder status is:

```text
READY_FOR_PHASE_2C_REAUDIT
```

use a different model/session.

Create:

```text
audit_v2/phase2c/rerun_01/
```

Do not overwrite the failed audit.

The re-audit should first reproduce the three original P1 defects:

```text
malformed monetary values
concurrent duplicate commit
dry-run side effect
```

Then rerun the Phase 2C release gate.

---

# 41. Mandatory Re-Audit Acceptance Cases

The independent re-audit must prove:

## Risk
```text
NaN → DENY/INVALID
negative → DENY/INVALID
missing currency → DENY/INVALID
wrong currency → DENY
100.01 > 100 → DENY
```

## Idempotency
```text
8 concurrent same-key same-request commits
→ exactly 1 side effect
```

and:

```text
same key + changed request
→ conflict
```

## Dry-run
```text
hostile mutating adapter
→ dry-run
→ zero side effects
```

Only then can these P1s be closed.

---

# 42. Final Builder Report

Report:

## 1. P1-01 — Risk Validation
- root cause;
- canonical value model;
- currency semantics;
- tests;
- mutations.

## 2. P1-02 — Atomic Idempotency
- root cause;
- atomic claim design;
- record state machine;
- concurrency results;
- lost-response behavior;
- persistence limitations.

## 3. P1-03 — Dry-Run Purity
- root cause;
- adapter contract change;
- planning vs active preview;
- side-effect-trap results.

## 4. `.agentnative-runs/`
- hygiene change;
- secret review.

## 5. Regression Results
- test counts;
- skipped;
- mutation counts;
- package checks.

## 6. Architecture / ADR Changes

## 7. Traceability / Threat Model Changes

## 8. Residual Risks

## 9. Status

Exactly one:

```text
READY_FOR_PHASE_2C_REAUDIT
PHASE_2C_REMEDIATION_NOT_READY
```

## 10. Next Action

If ready:

```text
Run independent Phase 2C re-audit with a different model.
Do not begin Phase 2D.
```

---

# Final Engineering Rule

The failed tests exposed three different systems principles:

```text
Malformed money bypass
→ validate domain semantics, not merely numeric comparison.

Concurrent duplicate commits
→ idempotency is an atomic coordination problem, not a dictionary lookup.

Mutating dry-run
→ simulation safety must come from architecture, not naming a method "preview".
```

Fix those principles at the boundary.

Then prove them under adversarial concurrency and hostile adapters.

Do not move to Phase 2D until the independent re-audit returns:

```text
PHASE_2C_READY
```

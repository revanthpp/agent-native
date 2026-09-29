# Agent Native v2 — Phase 2C Final Transaction-Identity Remediation
## Bind idempotency to authorization context, make confirmation replay-safe, and preserve exactly-once logical action semantics

## Current Status

The independent Phase 2C re-audit returned:

```text
PHASE_2C_NOT_READY
```

The original three P1 findings are now independently closed:

```text
Money / value / currency bypass        PASS
Concurrent same-request idempotency    PASS
Dry-run active mutation path           PASS
```

The remaining release blockers are narrower but still **HIGH severity**:

1. the idempotency fingerprint omits material authorization dimensions;
2. legitimate same-transaction retries are rejected because confirmation replay protection runs before idempotency replay resolution.

These two findings are related.

They expose one remaining architectural problem:

> **Agent Native does not yet have a fully defined identity for a logical transaction across authorization, confirmation, retry, and replay boundaries.**

Do not patch these as independent conditionals.

Define the transaction identity correctly, then make the pipeline obey it.

Do NOT start Phase 2D.

---

# 1. Authoritative Inputs

Read before modifying code:

```text
Agent_Native_v2_Product_BRD.md
PHASE_2C_RELEASE_REVIEW.md

audit_v2/phase2c/rerun_01/FINAL_PHASE_2C_REAUDIT.md
audit_v2/phase2c/rerun_01/findings.json
audit_v2/phase2c/rerun_01/RELEASE_GATE_MATRIX.md
audit_v2/phase2c/rerun_01/REMEDIATION_BACKLOG.md
audit_v2/phase2c/rerun_01/results/final_reaudit_checks.json

docs/architecture/PHASE_2C_ARCHITECTURE.md
docs/governance/TRANSACTION_SAFETY.md
docs/REQUIREMENTS_TRACEABILITY.md
docs/security/V2_THREAT_MODEL.md

src/agentnative/transactions/core.py
src/agentnative/simulator/engine.py
```

Also inspect canonical confirmation, policy, delegation, receipt, and trace models.

Do not alter the independent audit artifacts.

They describe the pre-remediation state.

---

# 2. Remediation Mission

This sprint has exactly three goals:

```text
A. Define a canonical logical transaction identity
B. Bind idempotency replay to material actor/environment/action dimensions
C. Make confirmation single-use across transactions but replay-safe within the same logical transaction
```

Do not add unrelated functionality.

Do not broaden Phase 2C scope.

---

# 3. Finding HIGH-01 — Idempotency Fingerprint Omits Material Authorization Dimensions

## Observed defect

The independent auditor changed:

```text
principal
agent
environment
```

while reusing the same idempotency key.

Agent Native replayed:

```text
EXECUTED
```

instead of failing closed.

This means the idempotency identity currently represents too little of the logical action.

This is dangerous because:

```text
same idempotency key
≠
same authorized transaction
```

unless the system binds the key to the actor and execution context.

---

# 4. Separate Two Concepts

Define two distinct concepts explicitly.

## 4.1 Idempotency key

A caller-provided or generated key used to identify retries.

Example:

```text
idem_123
```

It is NOT sufficient by itself to prove request equivalence.

## 4.2 Canonical logical transaction fingerprint

A deterministic hash over the **material semantic identity** of the action.

Conceptually:

```text
transaction_fingerprint =
HASH(
  business
  environment
  principal
  agent
  provider where applicable
  capability
  resource
  action payload
  amount
  currency
  quote identity
  confirmation identity where required
)
```

The exact model must align to existing BRD/domain types.

The idempotency record binds:

```text
idempotency_key
→ transaction_fingerprint
→ logical_transaction_id
```

---

# 5. Mandatory Fingerprint Dimensions

At minimum include:

```text
business_id
environment
principal_id
agent_id
capability_id
resource identity
normalized material action payload
```

Where applicable also bind:

```text
agent_provider
amount
currency
quote_id
confirmation_id
```

A change to any material execution dimension MUST NOT replay the previous transaction as though it were the same request.

---

# 6. Authorization Context vs Action Identity

Do not indiscriminately hash every piece of transient authorization evidence.

Distinguish:

## Material transaction identity

Who is acting, for whom, where, and what action is being requested.

These MUST be bound.

## Execution preconditions

Examples:

```text
policy version
delegation expiry
current authorization state
current ownership state
```

These may need to be revalidated at execution boundaries rather than necessarily embedded in the idempotency hash.

Document the distinction.

Avoid two bad outcomes:

### Too little binding

```text
different principal
same key
→ false replay
```

### Too much binding

```text
harmless retry metadata changes
→ false conflict
```

Create a deliberate canonicalization contract.

---

# 7. Canonical Fingerprint Rules

The canonical fingerprint MUST:

- be deterministic;
- use normalized typed values;
- canonicalize currency consistently;
- canonicalize resource identifiers;
- exclude unstable trace IDs;
- exclude timestamps that do not change transaction semantics;
- exclude transport-only headers;
- include every field whose change would materially alter authorization or side effect;
- never include raw secrets;
- use maintained cryptographic hashing;
- preserve enough debug evidence to explain a conflict without exposing raw sensitive payloads.

---

# 8. Fingerprint Adversarial Matrix

Using one idempotency key, change exactly one dimension at a time.

Required cases:

```text
principal
agent
provider if modeled
environment
business
capability
resource
amount
currency
quote
confirmation
material payload field
```

Expected:

```text
IDEMPOTENCY_CONFLICT
```

or an equivalent fail-closed outcome.

No second side effect.

No replay of a prior `EXECUTED` response pretending the changed request succeeded.

---

# 9. Fields That Should NOT Cause False Conflict

Test retries where only non-material metadata changes:

```text
trace ID
request timestamp
client retry counter
logging metadata
transport correlation headers
```

if those are not semantically part of the action.

Expected:

```text
same logical transaction
```

Document exact canonicalization behavior.

---

# 10. Actor/Environment Result Disclosure

A completed idempotent replay returns information about a prior transaction.

Therefore it must not leak that result to a different actor merely because the key matches.

Required invariant:

```text
same key
different principal/agent/environment
→ no prior result disclosure
```

Treat this as both:

```text
transaction-integrity
+
information-boundary
```

protection.

---

# 11. Finding HIGH-02 — Confirmation Replay Runs Before Idempotency Replay

## Observed defect

A legitimate retry uses:

```text
same logical request
same idempotency key
same confirmation
```

but confirmation replay protection fires first.

Result:

```text
CONFIRMATION_REPLAY
```

even though no new logical action should occur.

This confuses:

```text
replaying a confirmation for a NEW transaction
```

with:

```text
replaying the SAME transaction after transport uncertainty
```

These must have different semantics.

---

# 12. Confirmation Is Single-Use Per Logical Transaction

Replace the simplistic model:

```text
confirmation used once globally
```

with the stronger model:

> **A confirmation may authorize exactly one logical transaction. Retries/replays of that same logical transaction do not constitute a second use.**

Conceptually:

```text
confirmation_id
→ bound logical_transaction_id
```

Once bound:

```text
same transaction
→ replay-safe

different transaction
→ CONFIRMATION_REPLAY / DENY
```

---

# 13. Required Transaction Pipeline

The ordering must make idempotent replay possible without weakening confirmation controls.

A defensible conceptual sequence is:

```text
1. Authenticate / resolve actor context
2. Normalize material request
3. Compute canonical transaction fingerprint
4. Atomic idempotency lookup / claim
5. Branch on idempotency state
6. For NEW transaction:
      verify current ownership
      verify delegation
      evaluate policy
      verify quote / TOCTOU
      validate confirmation
      atomically bind confirmation to logical_transaction_id
      transition toward execution
7. Execute once
8. Persist outcome
9. Receipt / trace
```

For an EXISTING matching transaction:

```text
do NOT consume confirmation again
do NOT execute again
```

Instead branch on stored transaction state.

---

# 14. Existing Transaction Replay Semantics

For:

```text
same key
same fingerprint
```

define behavior by state.

## SUCCEEDED / EXECUTED

Return/replay the recorded outcome.

No new confirmation consumption.

No new business side effect.

## PENDING

Wait, return in-progress, or use documented bounded single-flight behavior.

No new confirmation consumption.

No new side effect.

## UNKNOWN_OUTCOME

Do not execute again automatically.

Return unknown/reconciliation-required semantics unless downstream verification can establish the prior outcome safely.

## FAILED_TERMINAL

Return terminal failure.

Do not execute again.

## FAILED_RETRYABLE

Retry behavior must be explicit.

If a new execution attempt is allowed for the **same logical transaction**, confirmation may remain bound to that transaction, but all required current execution preconditions must be handled according to BRD semantics.

Do not silently treat retryable failure as a brand-new transaction.

---

# 15. Confirmation Binding Record

Create or strengthen a canonical confirmation-consumption record.

Suggested conceptual fields:

```yaml
confirmation_id:
logical_transaction_id:
transaction_fingerprint:
principal_id:
agent_id:
business_id:
environment:
capability_id:
resource_id:
approved_value:
currency:
quote_id:
bound_at:
expires_at:
status:
```

Do not duplicate existing domain models unnecessarily.

Use existing structures where possible.

---

# 16. Atomic Confirmation Binding

Confirmation binding must be concurrency-safe.

Two different transactions attempting to bind the same confirmation concurrently must not both succeed.

Required:

```text
confirmation C1
transaction T1
transaction T2
```

At most one distinct logical transaction may own C1.

If T1 already owns C1:

```text
retry of T1 → allowed as replay
T2 → denied
```

---

# 17. Confirmation Expiry Semantics

Document exact semantics.

Distinguish:

## Completed transaction replay

If the action already succeeded while confirmation was valid:

```text
later transport replay
```

should be able to return the existing result even if the confirmation is now expired, because no new side effect occurs.

## New execution attempt

If no side effect occurred and execution is being attempted later, confirmation expiry may need to be re-evaluated.

Use BRD semantics.

Do not let "idempotency replay" become a mechanism to execute a previously unexecuted action after confirmation expiry.

---

# 18. Policy / Delegation Revocation on Replay

Distinguish:

```text
returning the result of an already-completed transaction
```

from:

```text
performing a new side effect
```

A completed replay should not re-execute because policy/delegation later changed.

An in-progress/retryable transaction attempting a fresh downstream execution must honor whatever revalidation the BRD requires at the commit boundary.

Document this explicitly.

---

# 19. Confirmation Replay Adversarial Matrix

Required tests:

### Same transaction retry

```text
same key
same fingerprint
same confirmation
prior outcome = SUCCEEDED
→ replay prior result
```

### Same transaction while PENDING

```text
same key
same fingerprint
same confirmation
→ wait/in-progress
```

### Different key, same action, same confirmation

```text
different logical_transaction_id
same confirmation
→ DENY
```

### Same key, changed amount, same confirmation

```text
fingerprint conflict
→ DENY
```

### Same key, changed principal, same confirmation

```text
fingerprint conflict
→ DENY
```

### Same key, changed environment, same confirmation

```text
fingerprint conflict
→ DENY
```

### New transaction after confirmation expiry

```text
→ DENY / REQUIRE_NEW_CONFIRMATION
```

### Completed transaction replay after confirmation expiry

```text
→ return existing outcome
→ no execution
```

---

# 20. Confirmation + Idempotency Race Test

Use concurrency.

Start multiple workers with:

```text
same key
same fingerprint
same confirmation
```

Expected:

```text
one logical transaction
one confirmation binding
one side effect
all other callers replay/wait coherently
```

Then start two DIFFERENT logical transactions concurrently with the same confirmation.

Expected:

```text
at most one confirmation binding
```

The loser must deny.

---

# 21. Lost Response Scenario After Confirmation

Mandatory:

```text
confirmation valid
idempotency claim acquired
confirmation bound to transaction
downstream action succeeds
response lost
caller retries same key/request/confirmation
```

Expected:

```text
no CONFIRMATION_REPLAY
no second side effect
recorded result / verification path returned
```

This is the exact interaction that currently fails and must be independently provable.

---

# 22. Request Fingerprint + Confirmation Identity

If `confirmation_id` is part of the canonical transaction fingerprint:

```text
same key
different confirmation
```

should conflict.

If the architecture intentionally excludes confirmation ID from fingerprint, provide a documented reason and prove an alternate binding prevents misuse.

Do not leave this accidental.

---

# 23. Request Fingerprint + Quote Identity

Apply the same reasoning to quote identity.

A request using the same idempotency key but a materially different quote must not replay the old transaction as though the new quote was processed.

Test:

```text
same key
quote Q1 → executed
quote Q2 → conflict
```

---

# 24. Idempotency Record Must Explain Conflict

When a fingerprint mismatch occurs, produce a structured conflict such as:

```text
IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST
```

Do not reveal the prior request's sensitive contents.

Safe evidence may include:

```text
idempotency key hash/reference
current transaction fingerprint hash
stored transaction fingerprint hash
conflict dimensions if safely derivable
```

Avoid raw secrets/PII.

---

# 25. Receipt Semantics for Replay

For a completed same-transaction replay:

Do NOT generate a second receipt that looks like a second business action unless explicitly marked as replay metadata.

Preferred:

```text
return original transaction receipt/reference
```

plus optional replay trace event.

Verify:

```text
one side effect
one canonical business-action receipt
multiple transport interactions
```

---

# 26. Trace Semantics for Replay

Trace should show:

```text
idempotency_replay_detected
existing_transaction_resolved
result_replayed
```

or equivalent.

It should NOT show another:

```text
execution_started
```

for a completed same-transaction replay.

---

# 27. UNKNOWN_OUTCOME + Confirmation

Test:

```text
confirmation bound
side effect may have occurred
outcome = UNKNOWN
retry same transaction
```

Do not reject merely as confirmation replay.

But also do not blindly execute again.

Expected:

```text
verification / reconciliation path
```

or documented equivalent.

---

# 28. Retryable Failure Before Side Effect

Test:

```text
confirmation bound
failure occurs before side effect
transaction = FAILED_RETRYABLE
same transaction retries
```

Define:

- whether same confirmation remains usable;
- whether expiry is rechecked;
- whether policy/delegation are rechecked;
- when a new confirmation is required.

Write this into ADR/documentation.

---

# 29. New Architecture Decision Record

Create an ADR covering:

```text
Logical Transaction Identity, Idempotency Scope, and Confirmation Replay Semantics
```

It should explain:

- idempotency key vs transaction fingerprint;
- material fingerprint dimensions;
- non-material excluded fields;
- logical transaction ID;
- atomic claim;
- confirmation binding;
- same-transaction replay;
- different-transaction replay denial;
- completed vs in-flight retry semantics;
- UNKNOWN_OUTCOME behavior;
- process-local limitations.

This is a first-class architecture decision.

---

# 30. Threat Model Updates

Update threats for:

## Cross-principal idempotency replay

```text
attacker/reuser supplies known key under different principal
→ prior result replay / auth boundary bypass
```

## Cross-agent replay

Same for agent/provider.

## Cross-environment replay

```text
sandbox/staging/prod context confusion
```

## Confirmation replay confusion

```text
legitimate same-transaction retry rejected
or
confirmation reused for a new transaction
```

For each map:

```text
preventive control
detective control
test
mutation
residual risk
```

---

# 31. Required Builder Tests — Fingerprint

Add canonical tests for:

```text
same key + same request → replay
same key + changed principal → conflict
same key + changed agent → conflict
same key + changed environment → conflict
same key + changed business → conflict
same key + changed capability → conflict
same key + changed resource → conflict
same key + changed amount → conflict
same key + changed currency → conflict
same key + changed quote → conflict
same key + changed confirmation → conflict or documented equivalent
same key + non-material trace metadata change → replay
```

---

# 32. Required Builder Tests — Confirmation Retry

Add:

```text
completed same-key retry with same confirmation → replay prior result
PENDING same-key retry → wait/in-progress, no replay error
different key same confirmation → deny
different transaction concurrent same confirmation → one winner
completed replay after confirmation expiry → return prior result
new execution after confirmation expiry → deny/new confirmation
lost-response retry → no confirmation replay + no duplicate effect
UNKNOWN_OUTCOME retry → no blind execution
```

---

# 33. Required Concurrency Tests

Run at minimum:

```text
8 workers × 25 rounds
```

for:

## Same key + same fingerprint + same confirmation

Expected:

```text
1 side effect
1 confirmation binding
0 confirmation replay failures for legitimate retries
```

## Same confirmation + distinct transaction IDs

Expected:

```text
<= 1 transaction obtains confirmation
```

## Same key + changed principal across workers

Expected:

```text
no cross-principal result replay
```

---

# 34. New Mutation Coverage

Add production-sensitive mutations for at least:

```text
M-IDEM-OMIT-PRINCIPAL
M-IDEM-OMIT-AGENT
M-IDEM-OMIT-ENVIRONMENT
M-IDEM-CONFIRMATION-ORDER
M-CONFIRMATION-CROSS-TX-REUSE
```

Names may differ.

Each must target canonical production code.

Expected:

- ordinary test suite catches every mutation;
- mutation restoration verified.

Do not count toy mutations.

---

# 35. Manual Builder Adversarial Tests

Before handoff, manually reproduce the two original HIGH findings.

## HIGH-01

Run:

```text
same key
request A principal=P1
request B principal=P2
```

Then repeat for:

```text
agent
environment
```

Expected:

```text
no replay
no side effect
conflict
```

## HIGH-02

Run:

```text
confirmed transaction
downstream succeeds
response lost
retry same key/request/confirmation
```

Expected:

```text
existing result replayed
no CONFIRMATION_REPLAY
one side effect
```

Record exact results.

---

# 36. Upstream Regression

Re-run critical Phase 2B / Phase 2C controls:

```text
identity
delegation
policy
confirmation binding
confirmation expiry
quote binding
TOCTOU
risk ceilings
atomic idempotency
lost response
partial outcomes
receipt integrity
trace correlation
redaction
```

Changing pipeline order can create subtle authorization regressions.

Do not assume earlier passes remain valid.

---

# 37. Clean Environment / Package Verification

Run:

```text
fresh editable install
pip check
full pytest
full unittest
wheel build
wheel install
package verifier
CLI smoke
```

For installed wheel, include at least:

```text
same-key completed retry
same-key changed-principal conflict
receipt verify
```

if practical through public APIs/CLI.

---

# 38. Independent Audit Evidence Must Remain Immutable

Do NOT modify:

```text
audit_v2/phase2c/rerun_01/
```

Create builder remediation documentation elsewhere.

Suggested:

```text
docs/remediation/PHASE_2C_TRANSACTION_IDENTITY_FIX.md
```

---

# 39. Builder Status

The builder must end with exactly one:

```text
READY_FOR_PHASE_2C_FINAL_REAUDIT
```

or:

```text
PHASE_2C_TRANSACTION_REMEDIATION_NOT_READY
```

Do not self-promote to:

```text
PHASE_2C_READY
```

Only the independent auditor closes that gate.

---

# 40. Final Independent Re-Audit Requirements

Use a fresh model/session.

Create a new evidence iteration:

```text
audit_v2/phase2c/rerun_02/
```

The auditor must first reproduce the original HIGH findings.

Minimum acceptance:

```text
same key + changed principal
→ conflict

same key + changed agent
→ conflict

same key + changed environment
→ conflict

completed confirmed same-key retry
→ result replay
→ no confirmation replay error
→ no second side effect
```

Then rerun the broader Phase 2C release matrix.

---

# 41. Release Gate

Phase 2C can become READY only if:

- both HIGH findings independently closed;
- transaction fingerprint covers all material identity/context dimensions;
- non-material retry metadata does not create false conflicts;
- confirmation is single-use across logical transactions;
- confirmation is replay-safe within the same logical transaction;
- completed retries never re-execute;
- PENDING retries do not consume confirmation again;
- same-key different-request fails closed;
- same-confirmation different-transaction fails closed;
- UNKNOWN_OUTCOME does not trigger blind re-execution;
- lost-response retry remains one logical side effect;
- receipts/traces represent replay accurately;
- no new HIGH/CRITICAL finding;
- clean package/regressions/mutations pass.

---

# 42. Required Builder Final Report

## 1. HIGH-01 Root Cause

Explain why principal/agent/environment were omitted.

## 2. Canonical Transaction Fingerprint

List included and intentionally excluded fields.

## 3. HIGH-01 Fix Evidence

Show changed-principal/agent/environment results.

## 4. HIGH-02 Root Cause

Explain pipeline ordering and why confirmation was consumed before replay resolution.

## 5. Confirmation Binding Model

Explain single-use-across-transactions vs replay-within-transaction semantics.

## 6. Pipeline Ordering

Show final sequence.

## 7. Lost Response Test

Show exact side-effect count and result.

## 8. Concurrency Results

Same transaction and competing transaction confirmation cases.

## 9. UNKNOWN_OUTCOME / Retryable Failure Semantics

## 10. Receipt / Trace Replay Semantics

## 11. Mutation Results

## 12. Full Regression Counts

Tests, subtests, skips, mutation totals, package checks.

## 13. ADR / Threat Model / Traceability Updates

## 14. Residual Risks

Especially process-local idempotency.

## 15. Status

Exactly:

```text
READY_FOR_PHASE_2C_FINAL_REAUDIT
```

or:

```text
PHASE_2C_TRANSACTION_REMEDIATION_NOT_READY
```

---

# Final Engineering Principle

These two findings are the same architectural problem viewed from opposite directions.

The first says:

```text
Two DIFFERENT authorized transactions
were accidentally treated as the SAME transaction.
```

The second says:

```text
The SAME logical transaction retry
was accidentally treated as a NEW confirmation use.
```

The fix is not another `if`.

The fix is a precise definition of:

> **What is a logical transaction?**

Once that identity is explicit, idempotency, confirmation, receipts, retries, and authorization can all agree on the same unit of work.

Do not move to Phase 2D until the independent re-audit proves they do.

# Agent Native v2 — Phase 2C Independent Adversarial Verification
## Simulator, Transaction Safety, Receipts, Recovery, and Observability Red-Team Audit

## Purpose

This document is the **independent Phase 2C audit directive** for Agent Native v2.

Builder-reported state:

```text
PHASE_2A_READY
PHASE_2B_READY
PHASE_2C_CONDITIONALLY_READY
PHASE_2D_NOT_STARTED
```

Reported Phase 2C implementation:

- verified-owner simulator;
- explicit lifecycle state machine;
- environment/risk ceilings;
- dry-run mode;
- preview/quote;
- TOCTOU protection;
- confirmation binding and replay protection;
- idempotency;
- bounded retries;
- partial outcomes;
- compensation;
- failure injection;
- tamper-evident minimized receipts;
- receipt verification CLI;
- redacted trace events;
- OpenTelemetry-compatible export;
- Phase 2C corpus;
- governance docs;
- ADRs;
- CI mutation checks.

Reported verification:

```text
pytest:              104 passed
subtests:            158 passed
Phase 2B mutations:  18/18 caught
Phase 2C mutations:  15/15 caught
wheel:               78 runtime files verified
CLI dry-run:         WOULD_ALLOW
CLI execution:       EXECUTED
receipt verification: VALID
```

Treat all of those as claims to verify independently.

The central Phase 2C question is:

> **Can Agent Native allow an authorized agent to perform a controlled action, prevent stale/duplicate/unauthorized execution, recover correctly when systems fail, and reconstruct exactly what happened afterward?**

Do not begin Phase 2D.

---

# 1. Role

Act as an independent:

- Principal Agent Systems Architect
- Distributed Systems Engineer
- Security Engineer
- Reliability Engineer
- QA / Evaluation Lead
- Release Gate Auditor

You did not build this implementation.

Your job is to attempt to prove it wrong.

---

# 2. Freeze production code

Do NOT modify:

```text
src/agentnative/
tests/
evals/
docs/
```

during the audit.

Create independent artifacts only under:

```text
audit_v2/phase2c/
```

You MAY use:

- temporary Git worktrees;
- temporary source copies;
- temporary HTTP servers;
- independent fixtures;
- audit-only monkeypatches;
- synthetic clocks;
- concurrency harnesses;
- temporary mutation copies.

Do not repair production defects during testing.

---

# 3. Read first

Read:

```text
Agent_Native_v2_Product_BRD.md
PHASE_2C_RELEASE_REVIEW.md
docs/architecture/PHASE_2C_ARCHITECTURE.md
docs/REQUIREMENTS_TRACEABILITY.md
docs/security/V2_THREAT_MODEL.md
docs/evals/PHASE_2C_EVALUATION_STRATEGY.md
docs/evals/PHASE_2C_ACCEPTANCE_THRESHOLDS.md
docs/governance/ACTIVE_TESTING.md
docs/governance/SIMULATION_ENVIRONMENTS.md
docs/governance/TRANSACTION_SAFETY.md
docs/governance/RECEIPT_RETENTION.md
```

Inspect:

```text
src/agentnative/simulator/
src/agentnative/transactions/
src/agentnative/receipts/
src/agentnative/observability/
```

and the Phase 2C mutation harness.

Reconstruct Phase 2C requirements independently before trusting traceability.

---

# 4. Required audit outputs

Create:

```text
audit_v2/phase2c/
  INDEPENDENT_PHASE_2C_AUDIT.md
  REQUIREMENTS_RECONSTRUCTION.md
  CLEAN_ENVIRONMENT_RESULTS.md
  STATE_MACHINE_RESULTS.md
  OWNERSHIP_ENVIRONMENT_RESULTS.md
  DRY_RUN_RESULTS.md
  PREVIEW_QUOTE_TOCTOU_RESULTS.md
  CONFIRMATION_RESULTS.md
  IDEMPOTENCY_RESULTS.md
  RETRY_FAILURE_RESULTS.md
  PARTIAL_COMPENSATION_RESULTS.md
  FAILURE_INJECTION_RESULTS.md
  RECEIPT_RESULTS.md
  OBSERVABILITY_RESULTS.md
  CONCURRENCY_RESULTS.md
  SECURITY_RED_TEAM.md
  MUTATION_RESULTS.md
  PACKAGE_RESULTS.md
  RELEASE_GATE_MATRIX.md
  REMEDIATION_BACKLOG.md
  findings.json
```

Do not fabricate PASS evidence.

---

# 5. Reconstruct requirements independently

For each Phase 2C requirement capture:

```yaml
requirement_id:
mandatory:
component:
expected_behavior:
security_boundary:
release_blocking:
```

Classify:

```text
MANDATORY
SHOULD
OPTIONAL
DEFERRED_TO_2D
DEFERRED_TO_V3
```

Compare to repository traceability.

Report missing requirements, false VERIFIED claims, missing code/tests/evals, and scope accidentally pulled forward from Phase 2D.

---

# 6. Clean environment reproduction

From a fresh environment run the repository-equivalent of:

```bash
python -m venv .audit-phase2c
source .audit-phase2c/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest
```

Also run the unittest path if supported.

Record:

```text
passed
failed
skipped
xfailed
subtests
warnings
```

Mandatory skipped tests block READY.

---

# 7. Built-wheel verification

Build a fresh wheel.

Create another clean environment.

Install the wheel and audit dependencies.

Verify:

```text
agentnative --help
agentnative simulate --help
agentnative receipts verify --help
```

Run at least:

- dry-run scenario;
- controlled execution scenario;
- denied scenario;
- receipt verification.

Installed behavior must match source-tree behavior.

---

# 8. State machine audit

Independently reconstruct the Phase 2C lifecycle.

Expected conceptual states may include:

```text
CREATED
OWNER_VERIFIED
AGENT_VERIFIED
DELEGATION_VERIFIED
CAPABILITY_RESOLVED
POLICY_EVALUATED
PREVIEWED
AWAITING_CONFIRMATION
AUTHORIZED
EXECUTING
EXECUTED
VERIFYING
SUCCEEDED
FAILED
PARTIAL
COMPENSATING
COMPENSATED
RECEIPT_CREATED
TERMINAL
```

Test every valid transition and deliberately attempt invalid ones:

```text
CREATED → EXECUTING
CREATED → SUCCEEDED
PREVIEWED → RECEIPT_CREATED
FAILED → EXECUTING
TERMINAL → EXECUTING
COMPENSATED → EXECUTING
```

Expected: reject without corrupting state.

Verify:

1. execution cannot precede ownership;
2. execution cannot precede identity/delegation/policy;
3. receipt cannot precede outcome;
4. compensation cannot precede an eligible state;
5. terminal state cannot resume execution;
6. history remains auditable;
7. invalid transition does not mutate state.

---

# 9. Ownership expiry / revocation during scenario

Test:

```text
ownership valid at start
→ preview
→ ownership expires or is revoked
→ commit attempted
```

For state-changing execution, verify required authority is checked at the correct boundary.

Expected behavior must be explicit and fail closed where the BRD requires it.

---

# 10. Environment boundary audit

Test:

```text
SANDBOX
STAGING
PRODUCTION_READ_ONLY
PRODUCTION_ACTIVE
```

Attack cases:

- production target mislabeled sandbox;
- mutation attempted in `PRODUCTION_READ_ONLY`;
- destructive execution attempted in `PRODUCTION_ACTIVE`;
- environment downgraded mid-scenario;
- sandbox authorization reused for production;
- production-read-only grant reused for staging mutation.

Phase 2C must not accidentally create an unrestricted production destructive-action path.

---

# 11. Risk ceiling audit

Test exact value boundaries:

```text
limit = 100
99.99
100.00
100.01
```

Also test:

- missing currency;
- wrong currency;
- negative values;
- huge values;
- floating-point boundary behavior;
- NaN/infinity if parsers permit them;
- value represented as string.

Malformed values must never bypass a ceiling.

---

# 12. Dry-run audit

Snapshot synthetic business state before and after:

```text
agentnative simulate ... --dry-run
```

Business state must remain unchanged.

Dry-run should still evaluate:

- ownership;
- identity;
- delegation;
- capability;
- policy;
- confirmation requirements;
- risk/value limits.

Expected vocabulary must clearly distinguish:

```text
WOULD_ALLOW
WOULD_DENY
WOULD_REQUIRE_HUMAN
```

from actual execution outcomes.

---

# 13. Dry-run side-effect traps

Create adapters where:

- `preview()` mutates;
- adapter initialization mutates;
- validation mutates;
- capability lookup mutates.

Verify the simulator either prevents/detects this according to the architecture, or explicitly documents the trust boundary.

Do not call dry-run safe without evidence.

---

# 14. Preview / commit separation

Test:

```text
preview → commit
```

and attempt:

```text
commit without preview
```

for capabilities requiring preview.

Also test:

```text
preview capability A
commit capability B
```

Expected: DENY.

---

# 15. Quote identity / expiry

Create a quote and alter one field at a time:

- capability;
- principal;
- resource;
- amount;
- currency;
- terms;
- environment;
- business;
- quote ID.

The original quote must not authorize a materially changed action.

Use a controllable clock to test:

```text
expiry - 1 ms
expiry
expiry + 1 ms
```

Also test malformed timestamps, offsets/time zones, future-created quote, and unrealistic expiry.

---

# 16. TOCTOU — value / resource changes

Mandatory cases:

```text
preview = $82
confirmation = $82
price changes to $95
commit
```

Expected: `REQUIRE_NEW_CONFIRMATION` or `DENY`.

Also test resource changes between preview and commit:

- inventory changed;
- booking slot removed;
- terms changed;
- version changed.

No silent stale commit.

---

# 17. Policy / delegation changes between preview and commit

Mandatory:

```text
policy v1 = ALLOW
preview succeeds
policy v2 = DENY
commit attempted
```

Expected: fail closed according to documented semantics.

Also:

```text
delegation valid
preview
delegation expires or is revoked
commit
```

Expected: DENY unless the BRD explicitly defines snapshot semantics.

---

# 18. Confirmation binding

Create confirmation for:

```text
capability = purchase
resource = X
amount = 82 USD
quote = Q1
principal = P1
```

Attempt reuse for:

- resource Y;
- 83 USD;
- 820 USD;
- capability B;
- quote Q2;
- principal P2;
- different environment.

Expected: `DENY` or `REQUIRE_NEW_CONFIRMATION`.

Test confirmation expiry and replay.

Old confirmation must not authorize a new material action.

---

# 19. Confirmation vs idempotency

Distinguish:

```text
retry same logical transaction
```

from:

```text
new transaction reusing old confirmation
```

The first may return the prior result.

The second must not create a new side effect.

---

# 20. Idempotency basic tests

Submit the exact same request twice with the same idempotency key.

Expected:

```text
one logical side effect
```

Verify stable result/reference and clear trace evidence.

Then reuse the same key with a different payload:

```text
K1 + $82
K1 + $900
```

Expected: conflict/rejection, never silent success.

---

# 21. Concurrent idempotency

This is mandatory.

Launch multiple concurrent commits with:

```text
same request
same idempotency key
```

Use threads, async tasks, or a controlled concurrency harness.

Verify exactly one side effect.

Sequential duplicate tests are not enough.

---

# 22. Idempotency across restart

If durable idempotency is claimed:

```text
commit
restart process
retry same key
```

must remain safe.

If Phase 2C intentionally uses in-memory state, document that limitation and ensure release language does not imply crash durability.

Assess against the BRD rather than assuming this is a blocker.

---

# 23. Lost-response scenario

Mandatory:

```text
commit request
→ downstream action succeeds
→ response lost
→ agent times out
→ agent retries
```

Expected:

```text
one logical side effect
```

This is one of the most important Phase 2C tests.

---

# 24. Ambiguous commit outcome

Inject connection loss after request dispatch where downstream success is unknown.

The system must not incorrectly claim definite failure if a side effect may have occurred.

Verify the state model can represent uncertainty/partial/verification-required semantics as documented.

---

# 25. Retry behavior

Verify:

- retryable vs terminal classification;
- maximum attempts;
- no infinite retry;
- idempotency identity preserved;
- terminal failures not retried.

Test invalid retry configuration:

- zero;
- negative;
- extremely large.

Also run a denial-of-wallet scenario where downstream always returns a retryable error. The system must stop.

---

# 26. Partial outcomes

Create:

```text
primary side effect succeeds
secondary step fails
```

Expected: `PARTIAL` when appropriate.

Do not accept false `SUCCEEDED` or false total `FAILED` if an irreversible side effect occurred.

---

# 27. Compensation

For reversible capabilities test:

```text
create → cancel
reserve → release
update → restore
```

Verify:

- compensation only offered where supported;
- compensation success changes state correctly;
- receipt/trace records original and compensating action.

Then force compensation failure.

It must not report `COMPENSATED`.

Test double compensation as well.

---

# 28. Failure injection

Trigger failures at:

1. before preview;
2. after preview;
3. before/after policy;
4. before/after confirmation;
5. before commit;
6. after commit before response;
7. during response;
8. before/during verification;
9. before/during compensation;
10. before receipt creation;
11. before trace finalization.

Verify state/evidence remain coherent.

Also verify failure-injection hooks are disabled by default and cannot be activated by target-controlled input.

---

# 29. Hidden mutation

Create a capability declared `READ` whose controlled adapter changes state.

Verify Agent Native detects/surfaces this if the BRD claims dynamic hidden-mutation detection.

If not generically detectable, confirm the limitation is explicit.

Never infer no side effects merely from method/description.

---

# 30. Receipt completeness

For relevant terminal states verify receipt semantics cover:

```text
receipt_id
timestamp
business/environment
agent/provider/principal
capability
policy ID/version
decision
delegation reference
confirmation reference
quote reference
request hash
result
side effect
resource
value/currency
correlation ID
trace ID
evidence refs
integrity
```

Use semantic equivalence if field names differ.

---

# 31. Receipt tamper tests

Modify one field at a time:

- amount;
- currency;
- result;
- resource;
- principal;
- agent;
- capability;
- policy version;
- trace ID;
- request hash;
- evidence reference.

`agentnative receipts verify` must reject tampering for integrity-covered fields.

---

# 32. Receipt canonicalization / authenticity

Test benign serialization variations:

- JSON key ordering;
- whitespace;
- newline changes;
- Unicode normalization where relevant.

Determine documented canonicalization semantics.

If receipts are signed, test wrong key / key rotation behavior.

If receipts are hash-only, ensure docs distinguish:

```text
tamper evidence
```

from:

```text
signer authenticity
```

Do not permit overclaiming.

---

# 33. Receipt privacy

Inject synthetic:

- bearer/access/refresh tokens;
- private-key-like strings;
- DPoP proof;
- full sensitive request body;
- PII-like identifier;
- card-like data;
- secrets in downstream error messages.

Inspect receipts and receipt verification output.

No raw secret should leak.

---

# 34. Receipt / trace substitution

Pair:

```text
receipt from transaction A
```

with:

```text
trace/evidence from transaction B
```

Verify mismatch is detected or clearly surfaced.

---

# 35. Observability completeness

Verify critical lifecycle events are reconstructable, such as:

```text
simulation_started
ownership_verified
identity_verified
delegation_verified
capability_resolved
policy_decided
preview_created
confirmation_requested
confirmation_received
execution_started
execution_succeeded / failed
retry_started
compensation_started / completed
receipt_created
simulation_completed
```

Exact event names may differ.

---

# 36. Trace correlation

Verify:

```text
scenario_id
trace_id
correlation_id
```

remain coherent across one logical transaction.

Retries should be distinguishable but tied to the same root transaction.

Verify receipt trace ID matches the actual trace.

---

# 37. OpenTelemetry compatibility

Do not accept something merely because it is named OpenTelemetry.

Inspect:

- trace IDs;
- span IDs;
- parent/child relationships;
- status/error semantics;
- timestamps;
- attributes;
- redaction.

If true OTel SDK/exporter interoperability is claimed, perform a real integration test where practical.

---

# 38. Observability secret safety

Inject secrets into request fields, errors, downstream responses, quote data, and confirmation metadata.

Inspect structured events and OTel export.

No raw secret should leak.

---

# 39. Concurrency isolation

Run multiple independent scenarios concurrently.

Verify:

- state does not leak;
- idempotency keys do not collide;
- confirmation A cannot satisfy B;
- receipts stay with the correct run;
- traces do not cross-contaminate;
- replay state is scoped correctly.

---

# 40. Concurrent policy / delegation changes

Test deterministic races such as:

```text
transaction A previews under policy v1
policy becomes v2
transaction A commits
transaction B starts
```

and:

```text
transaction A previews
delegation revoked
transaction A commits
```

No undefined accidental allow.

---

# 41. Time-boundary testing

Use injectable/fake time if possible.

Test exact boundaries for:

- ownership expiry;
- delegation expiry;
- quote expiry;
- confirmation expiry;
- replay window;
- policy effective/expiry;
- retry delays.

Avoid flaky sleeps.

If the architecture is not test-clock friendly, note maintainability risk.

---

# 42. Crash consistency

Where feasible, simulate restart/crash:

- after downstream success before local persistence;
- after state persistence before receipt;
- after receipt before trace finalization;
- during compensation.

If the reference implementation is intentionally in-memory, classify the limitation honestly and ensure it is not represented as durable production behavior.

---

# 43. Resource bounds

Safely test:

- large scenario input;
- large evidence set;
- repeated retryable errors;
- many trace events;
- many idempotency keys;
- many confirmations.

Look for uncontrolled memory/runtime growth.

Do not perform destructive load testing.

---

# 44. Target-controlled instructions

Inject prompt-injection-style text into:

- capability descriptions;
- quote metadata;
- downstream errors;
- receipt-facing metadata.

Verify target text remains data and cannot alter:

- policy;
- confirmation;
- retry;
- simulator state;
- risk ceiling.

---

# 45. Network / SSRF regression under active execution

If Phase 2C makes active network calls, retest:

- private IP;
- localhost;
- metadata endpoint;
- redirect to private target;
- cross-environment endpoint substitution;
- DNS-rebinding simulation where supported.

Phase 2C must not reopen SSRF paths closed earlier.

---

# 46. Credential boundary

Verify:

- credentials are scoped;
- credentials are not logged;
- credentials are not included in receipts/traces;
- sandbox credentials do not silently cross to production;
- target-controlled input cannot substitute privileged credentials.

---

# 47. Audit the 15/15 Phase 2C mutation claim

Inspect every mutation.

For each record:

```yaml
mutation_id:
claimed_control:
actual_production_target:
mutation_method:
expected_test_failure:
actual_test_failure:
restoration_verified:
meaningful:
```

Reject toy/dead-code/fake-copy mutations.

---

# 48. Required critical mutation coverage

Confirm real production-sensitive mutations cover at least:

1. bypass ownership gate;
2. bypass environment/risk ceiling;
3. allow commit without policy;
4. allow commit without confirmation;
5. disable confirmation binding;
6. disable confirmation replay prevention;
7. ignore quote expiry;
8. disable TOCTOU detection;
9. disable idempotency;
10. allow unbounded retry;
11. convert PARTIAL to SUCCESS;
12. suppress compensation failure;
13. accept modified receipt;
14. break trace correlation;
15. bypass receipt/trace redaction.

---

# 49. Independently mutate at least eight controls

In temporary audit copies independently break at least:

1. ownership gate;
2. risk ceiling;
3. confirmation binding;
4. quote expiry;
5. idempotency;
6. PARTIAL → SUCCESS;
7. receipt integrity;
8. trace redaction.

Run the normal suite.

Each should cause meaningful failures.

---

# 50. Property / invariant testing

Where practical, generate combinations for invariants:

```text
no valid authorization → no state change
same idempotency key + same request → <= 1 effect
same idempotency key + different request → conflict
expired confirmation → no commit
policy DENY → no commit
receipt tamper → invalid
terminal state → no execution transition
```

Use bounded, reproducible property tests.

---

# 51. Bounded fuzzing

Fuzz:

- state transitions;
- quote fields;
- confirmation fields;
- idempotency keys;
- receipt JSON;
- trace metadata.

Goal:

- no unexpected crash;
- no fail-open;
- no raw expected parser exception leak;
- no secret reflection.

Record random seed(s).

---

# 52. Phase 2A / 2B regressions

Rerun critical upstream controls because Phase 2C consumes them.

## Phase 2A
- protocol adapter error boundaries;
- safe remote refs;
- capability normalization.

## Phase 2B
- ownership;
- signature/replay;
- delegation;
- explicit DENY;
- default deny;
- policy version/staleness;
- OAuth/DPoP evidence semantics.

Phase 2C cannot be READY if it weakens an upstream gate.

---

# 53. Mandatory end-to-end scenarios

## Happy path

```text
verified owner
→ verified agent
→ valid delegation
→ capability resolved
→ policy allow/allow-with-limits
→ preview
→ confirmation if required
→ commit
→ verify
→ receipt
→ trace
```

## Lost response

```text
commit
→ downstream succeeds
→ response lost
→ retry
```

Expected: one logical effect.

## Stale value

```text
preview 82
→ confirmation 82
→ value changes to 95
→ commit
```

Expected: deny or new confirmation.

## Revocation

```text
preview
→ delegation revoked
→ commit
```

Expected: deny.

## Policy change

```text
preview under ALLOW
→ policy changes to DENY
→ commit
```

Expected: documented fail-closed result.

## Compensation

Run one successful compensation and one failed compensation.

Verify receipt and trace accurately distinguish outcomes.

---

# 54. Evidence integrity

For at least ten mandatory Phase 2C requirements manually trace:

```text
BRD
→ architecture / ADR
→ canonical code
→ test
→ eval
→ mutation where critical
→ release review
```

Any broken link is a finding.

---

# 55. False-confidence review

Specifically challenge:

```text
dry-run exists
≠ dry-run cannot mutate

idempotency model exists
≠ duplicate actions are impossible

bounded retries
≠ retries are safe

compensation declared
≠ rollback succeeds

receipt hash
≠ receipt authenticity

trace exists
≠ trace is complete/correct

OpenTelemetry-shaped data
≠ OTel interoperability

sandbox flag
≠ environment isolation
```

Document any overclaim.

---

# 56. Findings severity

Use:

```text
CRITICAL
HIGH
MEDIUM
LOW
INFO
```

Every finding:

```yaml
finding_id:
severity:
title:
requirement:
component:
reproduction:
expected:
actual:
evidence:
impact:
release_gate_impact:
recommended_remediation:
```

Do not inflate speculative concerns.

---

# 57. Final Phase 2C gate

Choose exactly one:

```text
PHASE_2C_READY
PHASE_2C_CONDITIONALLY_READY
PHASE_2C_NOT_READY
```

`PHASE_2C_READY` requires at minimum:

- clean environment reproducible;
- wheel-installed behavior verified;
- state machine correct;
- invalid transitions rejected;
- ownership/environment/risk ceilings enforced;
- dry-run proven non-mutating to the documented boundary;
- preview/commit contract correct;
- quote expiry correct;
- TOCTOU protections correct;
- confirmation binding/replay correct;
- delegation/policy checked at proper execution boundary;
- sequential and concurrent idempotency safe;
- lost-response retry safe;
- retries bounded;
- partial outcomes represented honestly;
- compensation success/failure represented honestly;
- failure injection isolated from target control;
- receipt tampering detected;
- receipt privacy passes;
- trace/receipt correlation passes;
- observability secret safety passes;
- production mutations meaningful;
- independent critical mutations caught;
- Phase 2A/2B regressions pass;
- no unresolved HIGH/CRITICAL Phase 2C finding.

---

# 58. Phase 2D is forbidden during audit

Do NOT implement Phase 2D.

If READY:

```text
PHASE_2C_READY

Independent Phase 2C verification complete.
Phase 2D may begin in a separate development cycle.
```

If not READY, produce remediation backlog.

---

# 59. Required release gate matrix

Use:

```text
PASS
FAIL
PARTIAL
NOT_VERIFIED
NOT_APPLICABLE
```

Include:

## Foundations
- clean install
- wheel install
- canonical package
- Phase 2A regressions
- Phase 2B regressions

## Simulator
- ownership gate
- environment boundary
- risk ceiling
- state machine
- dry-run

## Transaction Safety
- preview/commit
- quote identity
- quote expiry
- TOCTOU
- policy recheck
- delegation recheck
- confirmation binding
- confirmation replay
- idempotency
- concurrent idempotency
- retry bounds
- lost response
- partial outcomes
- compensation

## Evidence
- receipt completeness
- receipt tamper detection
- receipt privacy
- trace completeness
- trace correlation
- trace/receipt consistency
- OTel compatibility

## Resilience
- failure injection
- crash ambiguity
- resource bounds
- concurrency isolation

## Security
- network / SSRF boundary
- credential handling
- target content remains data
- mutation coverage
- evidence traceability

---

# 60. Remediation backlog format

Use:

```text
P0 — immediate / unsafe action possible
P1 — required before PHASE_2C_READY
P2 — required before Phase 2D
P3 — future hardening
```

Classify against the BRD and actual risk, not prior builder labels.

---

# 61. Final report format

## 1. Executive Verdict
`PHASE_2C: <exact status>`

Also reaffirm Phase 2A/2B after regression checks.

## 2. Clean Environment / Package Results

## 3. State Machine Results

## 4. Ownership / Environment / Risk Results

## 5. Dry-Run Results

## 6. Preview / Quote / TOCTOU Results

## 7. Confirmation Results

## 8. Idempotency / Concurrency Results

## 9. Retry / Lost Response Results

## 10. Partial / Compensation Results

## 11. Failure Injection Results

## 12. Receipt Results

## 13. Observability / OTel Results

## 14. Security Red-Team Results

## 15. Mutation Results

## 16. Upstream Regression Results

## 17. False-Confidence Risks

## 18. Findings by Severity

## 19. Release Gate Matrix

## 20. Remediation Backlog

## 21. Principal Engineer Assessment

Answer:

- Can Agent Native safely cross from policy evaluation into controlled action?
- What happens when downstream succeeds but the response is lost?
- Can concurrent retries create duplicate side effects?
- Can stale authorization, confirmation, quote, or policy reach commit?
- What exactly does a receipt prove?
- Can an operator reconstruct partial/failing transactions end to end?
- What remains reference-quality rather than production-grade?
- What would a Staff/Principal systems reviewer attack next?

## 22. Next Action

If READY:

```text
Freeze Phase 2C.
Create final v2 release-candidate evidence.
Only then design Phase 2D.
```

Otherwise:

```text
Remediate P0/P1 only and rerun this audit.
```

---

# Final Rule

Do not reward the build for having many tests.

Attack the distributed-systems invariants.

The Phase 2C release question is:

> **When authorization, time, networks, retries, concurrency, downstream systems, and humans all behave imperfectly at the same time, can Agent Native still prevent the wrong action, avoid duplicate action, recover honestly, and prove what happened?**

If the evidence says yes, mark Phase 2C READY.

If not, keep the gate closed.

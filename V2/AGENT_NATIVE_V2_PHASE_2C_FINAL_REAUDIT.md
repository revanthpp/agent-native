# Agent Native v2 — Phase 2C Final Re-Audit Directive
## Re-test the three P1 failures, adjudicate the concurrency-fixture dispute, and decide whether Phase 2C is actually READY

## Purpose

Run an **independent Phase 2C re-audit** after the second remediation.

This is not a build task.

Do not modify production code.

The previous independent stress audit returned:

```text
PHASE_2C_NOT_READY
```

with three release-blocking P1 findings:

1. malformed money/value/currency inputs could bypass risk ceilings;
2. concurrent idempotency was not atomic;
3. dry-run could mutate state.

The remediation builder now reports:

- exact `Decimal` monetary validation;
- rejection of NaN, infinity, negatives, booleans, numeric strings, missing/wrong currencies, oversized values;
- lowercase currency normalization;
- no FX conversion;
- atomic process-local idempotency claims;
- `PENDING`, success, retryable, terminal, and unknown states;
- same-key concurrent requests replay one result;
- changed request hashes fail closed;
- dry-run uses non-mutating `build_plan()`;
- dry-run does not call active `prepare()` / `preview()`;
- mutating plans are detected and denied;
- 25 rounds × 8 workers concurrency coverage;
- Phase 2C mutation harness expanded to `23/23 caught`;
- ADR-021 through ADR-023 added;
- traceability, threat model, governance, and `.agentnative-runs/` hygiene updated;
- `109 tests passed`, `158 subtests passed`;
- Phase 2B mutations `18/18`;
- wheel verification passed;
- installed-wheel CLI returned `WOULD_ALLOW`, `EXECUTED`, `VALID`, with correlated traces;
- `pip check` clean.

Builder status:

```text
READY_FOR_PHASE_2C_REAUDIT
```

The builder also reports:

> The original independent stress fixture remains untouched; its barrier-based fake adapter is incompatible with atomic pre-claim suppression. The corrected canonical builder stress test passes 8 workers × 25 rounds.

This statement MUST be independently adjudicated.

Do not assume the old fixture is wrong.

Do not assume the new implementation is wrong.

Determine which is true from the concurrency contract.

---

# 1. Role

Act as an independent:

- Principal Distributed Systems Engineer;
- Agent Systems Architect;
- Security Engineer;
- Transaction Safety Reviewer;
- QA / Evaluation Lead;
- Release Gate Auditor.

You did not build the remediation.

Your job is to establish the truth, not confirm the builder.

---

# 2. Production Freeze

Do NOT modify:

```text
src/agentnative/
tests/
evals/
docs/
```

Create all new evidence under:

```text
audit_v2/phase2c/rerun_01/
```

You may use:

- independent audit scripts;
- temporary worktrees;
- temporary copies;
- audit-only adapters;
- barriers/events/latches;
- controllable clocks;
- threads/processes/async workers;
- temporary mutations.

Do not repair defects during the audit.

---

# 3. Required Inputs

Read:

```text
Agent_Native_v2_Product_BRD.md
PHASE_2C_RELEASE_REVIEW.md

audit_v2/phase2c/INDEPENDENT_PHASE_2C_AUDIT.md
audit_v2/phase2c/findings.json
audit_v2/phase2c/REMEDIATION_BACKLOG.md
audit_v2/phase2c/RELEASE_GATE_MATRIX.md
audit_v2/phase2c/results/stress_checks.json

docs/architecture/PHASE_2C_ARCHITECTURE.md
docs/REQUIREMENTS_TRACEABILITY.md
docs/security/V2_THREAT_MODEL.md
docs/governance/TRANSACTION_SAFETY.md

ADR-021
ADR-022
ADR-023
```

Use actual repository paths for ADRs if naming differs.

Also inspect the canonical implementations for:

```text
money / risk evaluation
idempotency store / claim logic
simulator dry-run path
execution adapter interface
```

---

# 4. Required Outputs

Create:

```text
audit_v2/phase2c/rerun_01/
  FINAL_PHASE_2C_REAUDIT.md
  P1_RISK_RETEST.md
  P1_IDEMPOTENCY_RETEST.md
  P1_DRYRUN_RETEST.md
  CONCURRENCY_FIXTURE_ADJUDICATION.md
  LOST_RESPONSE_RETEST.md
  MUTATION_RETEST.md
  CLEAN_ENVIRONMENT_RETEST.md
  PACKAGE_RETEST.md
  PHASE_2C_RELEASE_GATE.md
  RELEASE_GATE_MATRIX.md
  REMEDIATION_BACKLOG.md
  findings.json
```

Do not overwrite the original failed audit.

---

# 5. First Principle

The three P1s must be tested as **invariants**, not as exact test fixtures.

The relevant invariants are:

```text
P1-01:
Malformed or semantically invalid monetary input cannot cross a monetary risk boundary.

P1-02:
For one logical state-changing request, concurrent retries using the same idempotency key cannot create more than one logical side effect.

P1-03:
Dry-run cannot invoke a path capable of producing external business-state mutation.
```

A builder can change implementation structure.

It cannot change these invariants without changing the BRD.

---

# 6. P1-01 — Monetary Risk Retest

Independently test the canonical monetary/risk boundary.

Do NOT only rerun builder tests.

Test at least:

```text
0
0.01
99.99
100.00
100.01
-0.01
-1
NaN
Infinity
-Infinity
None
True
False
"100"
"100.00"
"NaN"
very large Decimal
missing amount
missing currency
wrong currency
lowercase currency
whitespace currency
unknown currency
```

Use a ceiling such as:

```text
100.00 USD
```

Expected minimum behavior:

```text
99.99 USD → within ceiling
100.00 USD → within ceiling if inclusive is documented
100.01 USD → deny
NaN → invalid/deny
Infinity → invalid/deny
negative → invalid/deny unless capability explicitly permits signed amount
missing currency → invalid/deny
EUR against USD ceiling → deny
```

No malformed value may result in execution.

---

# 7. Money Representation Review

Inspect implementation.

Verify:

- comparison uses exact decimal semantics appropriate to the stated design;
- booleans do not pass because Python treats `bool` as a numeric subtype;
- string coercion is not silently accepted unless explicitly documented;
- non-finite values are rejected before comparison;
- currency normalization is deterministic;
- unknown currency does not become a wildcard;
- no implicit FX conversion occurs.

Report whether the implementation matches ADR-021 and BRD semantics.

---

# 8. Money Mutation Retest

Inspect the new monetary mutations.

At minimum independently verify tests are sensitive to:

```text
finite-value validation bypass
negative-value validation bypass
currency mismatch bypass
missing currency bypass
ceiling comparison bypass
```

Perform at least one manual audit mutation outside the builder harness.

Normal tests must fail.

---

# 9. P1-02 — Atomic Idempotency Retest

This is the highest-risk retest.

Do not use one concurrency harness.

Use **three independent concurrency designs**.

The invariant:

> same logical request + same idempotency key + concurrent arrival = at most one side effect.

---

# 10. Concurrency Harness A — Start Barrier Before Transaction Call

Create N workers.

All workers:

```text
construct same request
wait at audit barrier
simultaneously call Agent Native transaction API
```

The adapter itself should not contain a barrier.

Recommended N:

```text
8
32
```

Run multiple rounds.

Expected:

```text
side_effect_count == 1 per round
```

This is the primary concurrency test.

---

# 11. Concurrency Harness B — Slow Side Effect

Use an adapter whose actual execute method:

```text
increments an invocation counter
signals execution_started
blocks on an audit-controlled event
then performs one synthetic business mutation
```

Start many same-key workers while the owner is blocked inside execution.

Expected:

- only one worker enters the execution method;
- other workers do not perform side effects;
- waiting/replay semantics match documentation;
- release event lets owner complete;
- all callers resolve coherently.

This directly tests single-flight behavior while the winning request is `PENDING`.

---

# 12. Concurrency Harness C — Scheduler Pressure

Run repeated same-key races under variable timing.

Examples:

```text
8 workers × 100 bounded rounds
random small audit-only scheduling jitter
```

Use a fixed seed for reproducibility.

Track:

```text
round
workers
execution_count
side_effect_count
result_count
conflict_count
errors
```

Required:

```text
duplicate_side_effect_rounds = 0
```

Do not require identical return timing from all callers if contract permits waiting/in-progress semantics.

---

# 13. Adjudicate the Old Barrier Fixture

The builder says:

> the original barrier-based fake adapter is incompatible with atomic pre-claim suppression.

Determine precisely why.

Answer these questions in:

```text
CONCURRENCY_FIXTURE_ADJUDICATION.md
```

1. Where is the barrier located?
2. Does the barrier require multiple workers to enter a method that correct single-flight logic should permit only one worker to enter?
3. Does the old fixture deadlock/fail because it assumes all workers reach `execute()`?
4. Was that assumption part of the BRD?
5. Does removing the fixture weaken the actual idempotency invariant?
6. Can the original invariant be tested with a barrier placed **before** the transaction call instead?
7. Is the builder's replacement test adversarial enough?
8. Does an independent harness reproduce exactly one side effect?

Classify the old fixture as exactly one:

```text
VALID_DEFECT_REPRODUCER
INVALID_AFTER_ARCHITECTURE_CHANGE
TEST_DESIGN_FLAW
PARTIALLY_VALID
```

Do not dismiss it merely because it no longer fits the implementation.

---

# 14. Same Key + Different Request

Mandatory:

```text
key K1
request A
```

then concurrently and sequentially:

```text
key K1
request B
```

where B differs materially in one field at a time:

- amount;
- currency;
- resource;
- principal;
- agent;
- capability;
- environment;
- quote;
- confirmation;
- payload.

Expected:

```text
IDEMPOTENCY_CONFLICT / DENY
```

No second side effect.

No silent replay that misrepresents B as successful.

---

# 15. Request Hash Audit

Inspect canonical request hashing.

Verify material fields are bound.

Attempt collisions by changing fields believed not to be covered.

Report any material request dimension excluded from the hash.

Also verify unstable metadata such as timestamps/traces do not unnecessarily make legitimate retries hash differently.

---

# 16. Owner Failure Before Side Effect

Force the claim owner to fail before the downstream side effect begins.

Verify documented recovery semantics.

Determine:

- does record remain `PENDING` forever?
- can another worker retry?
- is failure terminal/retryable?
- can stale claim be recovered safely?

No duplicate effect is possible in this case, but liveness still matters.

---

# 17. Owner Failure After Side Effect

Mandatory ambiguity case:

```text
claim acquired
downstream side effect succeeds
local result persistence fails
```

Verify system does NOT simply free the key and permit an immediate second side effect.

Expected semantic state should be something like:

```text
UNKNOWN_OUTCOME
```

if outcome cannot be verified.

Test retry behavior.

This is as important as the normal concurrency race.

---

# 18. Lost Response After Successful Commit

Repeat the critical scenario after remediation:

```text
downstream action succeeds
response is lost
caller retries same key/request
```

Expected:

```text
one logical side effect
```

Verify receipt/trace/result semantics remain coherent.

---

# 19. Process-Local Limitation

The builder explicitly reports **process-local idempotency**.

Verify documentation says so.

Do NOT fail Phase 2C merely because it is not distributed/durable unless the BRD requires that.

But test and document:

```text
process restart
→ in-memory claim/result lost
```

Classify this as:

```text
documented reference limitation
```

or a release blocker based on the actual BRD.

Do not let the project call process-local coordination "production distributed idempotency."

---

# 20. Idempotency Deadlock / Liveness

Test:

- owner hangs;
- waiting callers time out;
- owner raises;
- result publication fails.

Verify waiters do not hang forever.

Bounded waiting/timeout semantics should be explicit.

A system that prevents duplicates by deadlocking every retry is not correct.

---

# 21. Idempotency Mutation Retest

Inspect production mutations for at least:

```text
remove atomic claim
move claim after execute
ignore request hash conflict
prematurely clear PENDING
```

Run them.

Then independently perform one manual atomicity mutation.

Normal concurrency tests must catch it.

---

# 22. P1-03 — Dry-Run Purity Retest

Independently instrument an execution adapter with counters for:

```text
constructor
build_plan
prepare
preview
execute
verify
compensate
```

Call dry-run.

Record exact methods invoked.

Expected contract should show:

```text
build_plan may run
prepare must not run
active preview must not run
execute must not run
compensate must not run
```

unless the updated architecture defines another explicitly pure method.

---

# 23. Hostile Mutating Active Adapter

Create an audit adapter whose:

```text
prepare()
preview()
execute()
```

all mutate a synthetic business-state counter.

Dry-run must produce:

```text
business_state_delta == 0
```

and those active methods must have invocation count zero.

---

# 24. Hostile Mutating `build_plan()`

The builder reports:

> mutating plans are detected and denied.

Test this claim carefully.

Create a `build_plan()` implementation that mutates:

- adapter-local state;
- synthetic external business state;
- a shared test store.

Determine what Agent Native can actually detect.

Important distinction:

```text
detecting that returned plan describes a mutation
```

is not the same as:

```text
detecting that build_plan() already mutated an external system
```

If arbitrary adapter code can perform an external side effect inside `build_plan()`, Agent Native generally cannot undo that after the fact.

The architecture should therefore define `build_plan()` as a **trusted/pure adapter contract**, not claim magical generic detection of arbitrary hidden side effects.

Report any overclaim.

---

# 25. Dry-Run Purity Boundary

Determine the exact security model:

```text
Is build_plan() trusted code?
Is it sandboxed?
Is outbound network blocked?
Is mutation detection structural or observational?
```

The release claim should be no stronger than the evidence.

A defensible Phase 2C claim might be:

> Dry-run never invokes Agent Native's active execution methods; adapter `build_plan()` is contractually required to be pure.

That is different from:

> Dry-run can safely execute arbitrary untrusted adapter code without side effects.

Make sure docs say the correct one.

---

# 26. Dry-Run Network Behavior

Observe outbound requests during dry-run.

Verify whether `build_plan()` can make network calls.

If network calls are permitted:

- verify NetworkPolicy still applies;
- document allowed purpose;
- ensure active mutation endpoints are not called by Agent Native's own path.

If dry-run is intended to be local-only, any outbound call is a defect.

Use BRD/ADR-023 to decide.

---

# 27. Dry-Run Result Honesty

Verify dry-run does not fabricate evidence it did not observe.

Examples:

If active remote quote is not called:

```text
remote_quote = NOT_OBSERVED_IN_DRY_RUN
```

or equivalent.

Do not report a remotely verified quote if only local planning occurred.

Test:

```text
WOULD_ALLOW
WOULD_DENY
WOULD_REQUIRE_HUMAN
```

all with state snapshots.

---

# 28. Dry-Run Mutation Retest

Inspect mutations that:

```text
route dry-run into active preview
route dry-run into prepare
route dry-run toward execute
```

At least one manual audit mutation must be performed.

Normal tests must catch it.

---

# 29. Regression — Risk + Confirmation Interaction

Use valid amount/currency.

Verify:

```text
value within ceiling
but confirmation required
→ still REQUIRE_HUMAN
```

Risk validation must not accidentally bypass confirmation logic.

---

# 30. Regression — Risk + Quote / TOCTOU

Test:

```text
preview 99 USD
confirmation 99 USD
commit value becomes 101 USD
```

Expected:

```text
DENY / NEW_CONFIRMATION
```

The new `Decimal` model must remain integrated with TOCTOU controls.

---

# 31. Regression — Idempotency + Confirmation

Test:

```text
same logical retry
same confirmation
same key
```

Expected one logical effect.

Then:

```text
new transaction
old confirmation
new key
```

Expected confirmation replay/binding rules to deny.

Atomic idempotency must not weaken confirmation semantics.

---

# 32. Regression — Idempotency + Policy Change

Scenario:

```text
request begins under policy ALLOW
idempotency claim acquired
policy becomes DENY before commit
```

Verify documented execution-boundary semantics.

Atomic claim does not itself equal authorization.

The final commit must still honor required policy re-check semantics.

---

# 33. Regression — Idempotency + Delegation Revocation

Same pattern:

```text
claim acquired
delegation revoked
commit boundary
```

Verify fail-closed behavior required by BRD.

---

# 34. Regression — Receipt / Trace

For:

- successful owner request;
- replaying waiter;
- same-key conflict;
- unknown outcome;
- denied malformed money request;
- dry-run;

verify receipt/trace semantics are correct.

Do not create a success receipt for a request that merely replayed/conflicted unless the schema explicitly represents that relation.

---

# 35. Clean Environment

Run fresh:

```bash
python -m venv .phase2c-rerun
source .phase2c-rerun/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest
```

Run unittest if supported.

Record counts, skips, warnings.

Mandatory skips block READY.

---

# 36. Installed Wheel

Build and install the wheel into a new environment.

Run:

- one malformed money denial;
- one dry-run;
- one successful execute;
- one same-key replay if CLI/API harness permits;
- receipt verify;
- trace correlation smoke.

Verify the fixes exist in the distributed artifact.

---

# 37. Full Mutation Suites

Run:

```text
Phase 2B mutations
Phase 2C mutations
```

Expected builder claims:

```text
18/18
23/23
```

Inspect the 23 Phase 2C mutations for production relevance.

Do not certify a count if mutations do not hit actual production seams.

---

# 38. Repeat the Original Three P1s First

Before broader sign-off, report explicitly:

| Original P1 | Retest | Result |
|---|---|---|
| malformed value/currency bypass | independent hostile money cases | PASS/FAIL |
| concurrent idempotency race | independent same-key races | PASS/FAIL |
| dry-run state mutation | hostile mutating adapter | PASS/FAIL |

All three must PASS before `PHASE_2C_READY` is possible.

---

# 39. Release Gate

Choose exactly one:

```text
PHASE_2C_READY
PHASE_2C_CONDITIONALLY_READY
PHASE_2C_NOT_READY
```

`PHASE_2C_READY` requires:

- all three original P1s independently closed;
- no unresolved HIGH/CRITICAL finding;
- no unresolved P1;
- concurrency produces at most one side effect;
- same key/different request conflicts;
- unknown-outcome behavior is safe;
- waiting callers have bounded/liveness semantics;
- dry-run invokes no active execution path;
- dry-run claims match actual trust boundary;
- malformed monetary inputs fail closed;
- TOCTOU/confirmation/policy/delegation regressions pass;
- receipts/traces remain coherent;
- clean install/wheel pass;
- mutation suites remain meaningful.

---

# 40. Phase 2D remains forbidden

Do NOT implement Phase 2D.

If READY:

```text
PHASE_2C_READY

The three original P1 findings are independently closed.
Phase 2C may be frozen as the completed v2 controlled-action layer.
Phase 2D may be designed in a separate cycle.
```

If not READY:

produce a narrowly scoped remediation backlog.

---

# 41. Required Final Report

## 1. Executive Verdict

```text
PHASE_2C: ...
```

## 2. Original P1 Closure Matrix

## 3. Monetary Risk Results

## 4. Atomic Idempotency Results

Include:

- Harness A;
- Harness B;
- Harness C;
- exact side-effect counts;
- changed-request conflicts;
- liveness;
- unknown outcome;
- lost response.

## 5. Original Fixture Adjudication

Explain whether the old barrier fixture was valid or flawed, and why.

## 6. Dry-Run Purity Results

Include exact method invocation counts and state deltas.

## 7. Dry-Run Trust Boundary

State exactly what purity is guaranteed and what is contractually trusted.

## 8. Cross-Control Regressions

Risk/TOCTOU, idempotency/confirmation, policy, delegation.

## 9. Receipt / Trace Results

## 10. Clean Environment / Wheel

## 11. Mutation Results

## 12. New Findings

Use CRITICAL/HIGH/MEDIUM/LOW/INFO.

## 13. Release Gate Matrix

Use PASS/FAIL/PARTIAL/NOT_VERIFIED/NOT_APPLICABLE.

## 14. Remediation Backlog

P0/P1/P2/P3.

## 15. Principal Engineer Assessment

Answer:

- Is monetary risk now modeled as a domain invariant rather than a loose numeric comparison?
- Is idempotency truly atomic or merely test-shaped?
- What happens if the idempotency owner crashes after the real side effect?
- Does dry-run have an architectural purity boundary?
- Is the builder's claim about the old barrier fixture correct?
- What remains process-local/reference-grade?
- Is there any evidence/release-language overclaim?

## 16. Next Action

If READY:

```text
Freeze Phase 2C and prepare the v2 release-candidate evidence package.
Do not begin Phase 2D in this audit.
```

Otherwise:

```text
Remediate only the remaining release blockers and rerun this audit.
```

---

# Final Rule

The builder claims the original three P1s are fixed.

Do not test the implementation shape.

Test the invariants.

Especially:

```text
8 or 32 concurrent callers
same logical request
same idempotency key
→ one side effect
```

and:

```text
dry-run
→ no active execution path
→ zero business-state side effects attributable to Agent Native's execution flow
```

and:

```text
invalid money semantics
→ never reaches execution
```

If those survive independent adversarial testing, Phase 2C has earned another READY decision.

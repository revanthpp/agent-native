# Agent Native v2 — Phase 2B Closure Build Directive
## Compatibility Bridge Removal, DPoP Completion, Production-Control Mutation Wiring, and Canonical Root Cleanup

## Purpose

This file is the execution directive for the **final Phase 2B closure sprint** of Agent Native v2.

Current reported state:

```text
PHASE_2A_READY
PHASE_2B_CONDITIONALLY_READY
```

Reported completed Phase 2B capabilities include:

- Ed25519 HTTP request-signature verification;
- method, target URI, and content-digest coverage;
- timestamp, nonce, replay-window, and key/agent binding;
- cryptographic identity promotion only after successful verification;
- OAuth evidence classification;
- immutable policy versions and audit records;
- explicit `DENY` precedence over broad `ALLOW`;
- delegation scope analysis;
- repeatable mutation harness;
- additional ownership, signature, replay, policy, and adversarial tests;
- root namespace compatibility exports and CLI integration;
- `cryptography` as a runtime dependency;
- v2 test suite passing;
- v1 regression suite passing;
- package installation, `pip check`, compilation, and CLI smoke passing.

Remaining reported blockers:

1. remove the temporary `agentnative_v2` compatibility bridge;
2. complete sender-constrained-token / DPoP assessment;
3. wire mutation cases directly to real production controls;
4. remove duplicate incubation implementation after root verification.

This directive exists to close those blockers only.

Do NOT begin Phase 2C.

The authoritative product source of truth remains:

```text
Agent_Native_v2_Product_BRD.md
```

---

# 1. Role

Act as Principal Engineer, Security Architect, Identity/Authorization Architect, Release Engineer, and Evaluation Lead.

Your objective is:

> **Turn Phase 2B from CONDITIONALLY_READY into independently testable READY by removing temporary architecture debt and proving that the implemented security controls are real, canonical, and test-sensitive.**

Do not add unrelated features.

Do not expand into simulator, transaction, receipt, or sector work.

---

# 2. Phase 2B Closure Principles

Preserve these principles:

1. one canonical production implementation;
2. one canonical package namespace;
3. identity is separate from authorization;
4. authorization is separate from policy;
5. state-changing actions fail closed;
6. cryptographic verification must be real, not declarative;
7. sender-constrained token results must not overstate evidence;
8. mutation testing must defeat real production controls;
9. v1 security invariants must survive;
10. no critical/high unresolved issue may remain at closure.

---

# 3. First Task — Verify Current Repository State

Before modifying code:

1. inspect Git status;
2. confirm branch is `develop/v2` or equivalent;
3. confirm `v1.0.0` tag remains intact;
4. identify root package path;
5. identify all remaining `agentnative_v2` imports;
6. identify all remaining `/v2` implementation modules;
7. identify whether packaging includes duplicate modules;
8. identify whether tests are exercising root code or compatibility wrappers.

Create:

```text
docs/migration/PHASE_2B_FINAL_CANONICALIZATION_AUDIT.md
```

Include:

| Item | Current Source | Canonical Target | Action |
|---|---|---|---|
| protocol adapters | ... | ... | KEEP/MERGE/REMOVE |
| ownership | ... | ... | ... |
| identity | ... | ... | ... |
| delegation | ... | ... | ... |
| policy | ... | ... | ... |
| security | ... | ... | ... |
| tests | ... | ... | ... |
| evals | ... | ... | ... |

---

# 4. Remove `agentnative_v2` Compatibility Bridge

## Requirement

At Phase 2B completion:

```text
src/agentnative/
```

must be the only production implementation namespace.

There MUST NOT be production imports from:

```text
agentnative_v2
```

or equivalent temporary compatibility modules.

## Actions

Search repository-wide for:

```text
agentnative_v2
v2/src
compat
bridge
```

Classify every reference:

```text
PRODUCTION
TEST
DOCUMENTATION
HISTORICAL
```

Production references MUST be removed.

Historical documentation MAY retain references when clearly labeled.

## Verification

Required automated check:

```text
test_no_production_agentnative_v2_imports
```

The test must scan production Python source and fail if the deprecated namespace appears.

Package-build inspection must also prove the old namespace is not shipped.

---

# 5. Remove Duplicate Incubation Implementation

Do NOT blindly delete `/v2`.

First prove parity.

For every module promoted to root:

1. compare root implementation vs incubation copy;
2. identify differences;
3. preserve the more complete/correct implementation;
4. run relevant tests;
5. remove duplicate only after verification.

After cleanup:

```text
/v2
```

MAY contain only:

- archived prompts;
- migration notes;
- historical review artifacts;

if explicitly desired.

It MUST NOT contain an alternate production package.

Preferred archival location:

```text
docs/history/v2-incubation/
```

or Git history only.

---

# 6. Package Artifact Verification

Build the wheel/sdist.

Inspect package contents.

Required result:

- exactly one Agent Native runtime package;
- no `agentnative_v2` package;
- no duplicated protocol modules;
- no duplicated policy modules;
- no incubation source tree packaged.

Create:

```text
scripts/verify_package_contents.py
```

or equivalent.

CI must execute it.

---

# 7. DPoP / Sender-Constrained Token Assessment

Complete the BRD-scoped sender-constrained-token assessment.

Do NOT build an OAuth authorization server.

Do NOT invent a proprietary proof format.

The purpose is to:

> detect, classify, and where controlled evidence is available, verify sender-constrained token properties.

---

# 8. DPoP Result Semantics

Results MUST distinguish:

```text
DECLARED
OBSERVED
VERIFIED
NOT_OBSERVED
UNSUPPORTED
INVALID
```

Definitions:

## DECLARED
Metadata claims DPoP/sender-constrained-token support.

## OBSERVED
Relevant protocol evidence is present, but cryptographic/runtime validation was not completed.

## VERIFIED
A controlled proof was cryptographically validated against the expected key, method, target, and freshness/replay requirements.

## NOT_OBSERVED
No relevant evidence found.

## UNSUPPORTED
Target/profile explicitly does not support the assessed mechanism or Agent Native adapter cannot assess it.

## INVALID
Relevant proof/evidence is present but fails validation.

Do NOT collapse these states.

---

# 9. DPoP Verification Scope

Where controlled verification is supported, validate:

- proof signature;
- key binding;
- `htm` / HTTP method binding;
- `htu` / target URI binding;
- issued-at/freshness;
- proof identifier / replay prevention;
- access-token hash binding when applicable;
- nonce handling when applicable.

Do not overclaim properties that the current implementation cannot verify.

---

# 10. DPoP Adversarial Cases

Add tests/evals for:

1. valid proof;
2. wrong signing key;
3. modified method;
4. modified URI;
5. stale proof;
6. future-dated proof;
7. replayed proof;
8. duplicate proof ID;
9. access-token hash mismatch where applicable;
10. malformed JWK;
11. unsupported algorithm;
12. missing required claim;
13. wrong nonce;
14. proof issued for Agent A used by Agent B context;
15. declared support with no proof available.

Expected outcome must be explicit for every case.

---

# 11. No False Confidence in OAuth / DPoP Reporting

Required invariant:

```text
OAuth metadata exists
≠
OAuth behavior verified
```

and:

```text
DPoP declared
≠
sender-constrained token verified
```

Add regression tests that prevent:

```text
DECLARED → VERIFIED
```

without actual verification evidence.

---

# 12. Mutation Harness — Production Control Wiring

The current mutation harness is reported as repeatable but not yet wired directly to production controls.

Fix this.

Mutation testing MUST alter or bypass the **actual production decision path**.

It MUST NOT test:

- duplicate toy functions;
- fake security wrappers;
- mutation-only copies;
- stand-alone reference implementations disconnected from runtime.

---

# 13. Required Production Control Mutations

At minimum mutate real controls for:

1. ownership verification;
2. HTTP signature verification;
3. replay protection;
4. delegation expiry;
5. delegation revocation;
6. principal binding;
7. agent binding;
8. provider binding where required;
9. audience binding;
10. capability binding;
11. resource binding;
12. value ceiling;
13. explicit `DENY` precedence;
14. state-changing default deny;
15. policy version/staleness;
16. secret redaction.

For each:

```yaml
mutation_id:
production_control:
source_location:
mutation:
expected_tests:
actual_failed_tests:
caught:
```

---

# 14. Mutation Harness Safety

The harness MUST:

- operate on a temporary copy/worktree or controlled monkeypatch seam;
- never leave production source mutated;
- restore state after every mutation;
- fail if restore fails;
- produce deterministic output;
- return nonzero if a required mutation survives.

CI may run a selected critical mutation subset if full mutation execution is expensive.

The full release review MUST run all mandatory mutations.

---

# 15. Mutation Quality Requirement

A mutation is useful only if it represents a real defect.

Example good mutation:

```text
production policy resolver changes:
default DENY → ALLOW
```

Example weak mutation:

```text
change an unused helper constant
```

Every mandatory mutation must map to a real release/security invariant.

---

# 16. Policy Staleness Re-Verification

Even though policy audit/versioning is reported complete, re-run final closure cases:

```text
policy v1 = ALLOW
policy v2 = DENY
```

Verify:

- newly evaluated request uses v2;
- stale reference cannot silently authorize state-changing action;
- explicit policy version is recorded;
- audit history remains immutable;
- rule explanation references correct version.

Add a regression test if not already present.

---

# 17. Signature + Identity Re-Verification

Re-run final cases proving:

```text
CRYPTOGRAPHICALLY_VERIFIED
```

can only result from successful signature verification.

Test:

- constructing an identity object manually;
- invalid signature;
- expired key;
- wrong key;
- replayed request;
- identity from wrong provider.

No bypass should result in cryptographically verified state.

---

# 18. Delegation Re-Verification

Final closure matrix:

| Condition | Expected |
|---|---|
| valid grant | eligible for policy evaluation |
| expired | deny |
| revoked | deny |
| wrong principal | deny |
| wrong agent | deny |
| wrong provider | deny if constrained |
| wrong audience | deny |
| wrong capability | deny |
| wrong resource | deny |
| over value | deny |
| wrong geography | deny |
| insufficient scope | deny |

Overbroad scope MUST be surfaced according to BRD semantics.

---

# 19. State-Changing Fail-Closed Matrix

Create or confirm automated test:

| Identity | Signature | Delegation | Policy | Expected |
|---|---|---|---|---|
| missing | n/a | valid | allow | DENY |
| valid | invalid | valid | allow | DENY |
| valid | valid | missing | allow | DENY |
| valid | valid | expired | allow | DENY |
| valid | valid | valid | missing | DENY |
| valid | valid | valid | error | DENY |
| valid | valid | valid | explicit deny | DENY |
| valid | valid | valid | allow | ALLOW/controlled |

This is a Phase 2B core invariant.

---

# 20. Independent Package-Root Verification

After bridge/duplicate removal:

Perform a clean install from built wheel.

Then run:

```text
agentnative --help
agentnative scan --help
agentnative protocols --help
agentnative capabilities --help
agentnative owner --help
agentnative policy --help
```

Run representative Phase 2A and 2B behavior from installed artifact.

Do not count source-tree execution alone as packaging proof.

---

# 21. v1 Regression Re-Run

Run all v1 tests.

Then explicitly re-run critical invariants:

1. report boundary;
2. secret redaction;
3. file scheme block;
4. SSRF block;
5. redirect validation;
6. evidence provenance;
7. mutation-risk monotonicity;
8. malformed artifact observability;
9. nonzero fatal exit;
10. prompt-injection content treated as data.

All must pass.

---

# 22. Phase 2A Regression Re-Run

Re-run:

- JSON OpenAPI;
- YAML OpenAPI;
- safe `$ref`;
- malicious/cyclic refs;
- MCP;
- A2A;
- adapter isolation;
- capability graph equivalence;
- provenance.

All mandatory Phase 2A tests must remain green with zero mandatory skips.

---

# 23. CI Finalization

CI must now enforce:

```text
formatting
lint
typing
compile
unit
integration
protocol
ownership
identity
signature
replay
delegation
policy
OAuth/DPoP assessment
security
adversarial
selected critical mutations
package build
package content verification
clean install
CLI smoke
v1 regression
```

Mandatory skipped tests fail the gate.

---

# 24. Traceability Update

Update:

```text
docs/REQUIREMENTS_TRACEABILITY.md
```

Every Phase 2B mandatory item must map:

```text
requirement
→ architecture
→ production code
→ regression test
→ adversarial eval
→ mutation where applicable
→ release gate
```

Statuses must be honest:

```text
IMPLEMENTED
VERIFIED
PARTIAL
DEFERRED_BY_BRD
```

No mandatory blocker may remain `PARTIAL` for READY.

---

# 25. Threat Model Finalization

Update:

```text
docs/security/V2_THREAT_MODEL.md
```

Confirm final coverage for:

- ownership takeover;
- agent impersonation;
- provider impersonation;
- signature replay;
- DPoP replay;
- stolen delegation;
- cross-agent grant reuse;
- cross-principal grant reuse;
- confused deputy;
- scope escalation;
- audience confusion;
- policy bypass;
- stale policy;
- cross-protocol identity confusion;
- secret leakage.

Every threat must have:

```text
preventive control
detective control
test
eval
residual risk
```

---

# 26. Final Phase 2B Release Gate

Create/update:

```text
PHASE_2B_RELEASE_REVIEW.md
```

Phase 2B may be marked `READY` only if ALL are true:

- compatibility bridge removed from production;
- duplicate incubation runtime removed;
- canonical package confirmed;
- DPoP/sender-constrained assessment complete to BRD scope;
- no false VERIFIED results;
- mutation harness hits actual production controls;
- every mandatory critical mutation is caught;
- package artifact clean;
- v1 tests/invariants pass;
- Phase 2A regressions pass;
- Phase 2B tests/evals pass;
- no mandatory tests skipped;
- no critical/high unresolved defects;
- traceability complete.

Status exactly one:

```text
PHASE_2B_READY
PHASE_2B_CONDITIONALLY_READY
PHASE_2B_NOT_READY
```

---

# 27. Do Not Start Phase 2C

If status is:

```text
PHASE_2B_READY
```

STOP.

Do not begin Phase 2C in the same execution.

The next action is independent adversarial testing using the separate test directive.

If status remains conditional/not-ready:

STOP and report blockers.

---

# 28. Required Final Response

Report:

## 1. CANONICALIZATION
- bridge removal;
- duplicate removal;
- package namespace;
- package artifact inspection.

## 2. DPoP / SENDER-CONSTRAINED TOKEN
- implemented assessment;
- verified vs declared semantics;
- adversarial results.

## 3. MUTATION HARNESS
- production controls mutated;
- caught/not caught.

## 4. POLICY CLOSURE
- staleness/version/audit result.

## 5. SIGNATURE / IDENTITY
- cryptographic promotion proof.

## 6. DELEGATION
- final matrix.

## 7. TEST RESULTS
Counts by category.

## 8. EVAL RESULTS
Counts by category.

## 9. V1 / PHASE 2A REGRESSIONS
Pass/fail.

## 10. RESIDUAL RISKS
Explicit.

## 11. RELEASE GATE

Exactly one:

```text
PHASE_2B_READY
PHASE_2B_CONDITIONALLY_READY
PHASE_2B_NOT_READY
```

## 12. NEXT ACTION

If READY:

```text
Run independent Phase 2B red-team audit.
Do not begin Phase 2C until audit passes.
```

---

# 29. Engineering Standard

This is a closure sprint, not a feature sprint.

The key question is not:

> Did we add DPoP?

It is:

> Can the system distinguish claimed trust from verified trust, can every state-changing authorization fail closed, is there one canonical production path, and do our tests provably detect the loss of those controls?

Finish Phase 2B cleanly.

Then stop for independent verification.

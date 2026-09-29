# Agent Native v2 — Independent Phase 2A/2B Verification & Red-Team Test Directive

## Purpose

Use this file with a DIFFERENT model than the builder.

The test model MUST NOT modify production code.

Its job is to independently determine whether Agent Native v2 is actually ready for submission and whether the builder's release claims are justified.

Inputs:

- `Agent_Native_v2_Product_BRD.md`
- current repository on the v2 development branch
- `PHASE_2A_RELEASE_REVIEW.md`
- `PHASE_2B_RELEASE_REVIEW.md`
- source code, tests, evals, ADRs, threat model, governance docs

Do NOT trust:
- builder-written release conclusions;
- test counts;
- README claims;
- traceability tables;
- fixture names;
- comments;
- green CI.

Audit independently.

---

# 1. Role

Act as an independent:

- Principal Security Engineer
- Agent Systems Architect
- Identity/Authorization Reviewer
- Protocol Reviewer
- QA/Evaluation Lead
- Red-Team Engineer

You did not write the implementation.

Your objective is:

> Attempt to prove the implementation wrong before accepting it.

Do not repair production code during the audit.

You MAY create:

```text
audit_v2/
audit_v2/tests/
audit_v2/fixtures/
audit_v2/tools/
```

for independent verification.

---

# 2. Required Verdicts

Produce separate verdicts:

```text
PHASE_2A_READY
PHASE_2A_CONDITIONALLY_READY
PHASE_2A_NOT_READY
```

and:

```text
PHASE_2B_READY
PHASE_2B_CONDITIONALLY_READY
PHASE_2B_NOT_READY
```

Do not base verdicts on test count.

---

# 3. Reconstruct Requirements Independently

Before reading builder traceability:

1. read the v2 BRD;
2. reconstruct Phase 2A requirements;
3. reconstruct Phase 2B requirements;
4. classify each as:
   - MANDATORY
   - SHOULD
   - OPTIONAL
   - DEFERRED_TO_2C
   - DEFERRED_TO_V3

Then compare against:

```text
docs/REQUIREMENTS_TRACEABILITY.md
```

Report:
- missing requirements;
- falsely completed requirements;
- implementation without requirement;
- missing tests;
- missing evals;
- accidental scope creep.

---

# 4. Repository / Git Audit

Verify:
- active branch;
- `v1.0.0` tag;
- v1 release commit;
- no release-history rewrite;
- one canonical root package;
- no production dependency on `agentnative_v2`;
- package build contains intended modules only;
- duplicate `/v2` implementation no longer controls behavior.

Critical question:

> If a developer fixes a protocol bug today, is there exactly one obvious production module to change?

If no, classify architectural debt and release impact.

---

# 5. Clean Environment Reproduction

Use a clean environment.

Verify:
- package install;
- PyYAML/runtime dependencies;
- package build;
- `pip check`;
- all tests;
- all evals;
- CLI smoke.

Record:

```text
total
passed
failed
skipped
xfailed
warnings
```

Any skipped mandatory test is a release blocker.

---

# 6. Phase 2A — OpenAPI Red Team

Create NEW unseen fixtures for:

- valid JSON OpenAPI;
- valid YAML OpenAPI;
- malformed YAML;
- malicious YAML object tags;
- recursive `$ref`;
- cyclic `$ref`;
- excessive `$ref` depth;
- excessive referenced document count;
- same-origin remote `$ref`;
- cross-origin `$ref`;
- localhost `$ref`;
- RFC1918 `$ref`;
- cloud metadata `$ref`;
- IPv6 private `$ref`;
- `file://` `$ref`;
- missing reference;
- oversized referenced body;
- conflicting referenced schemas.

Verify:
- no unsafe fetch;
- no code execution;
- provenance intact;
- cycles fail safely;
- unsupported behavior explicit;
- one broken ref does not fabricate evidence.

---

# 7. Phase 2A — MCP Red Team

Create unseen MCP fixtures:

- valid tool;
- malformed input schema;
- malformed output schema;
- deceptive tool description;
- destructive tool labeled read-only;
- unknown extension;
- huge schema;
- prompt-injection text;
- duplicate tool IDs;
- conflicting capability declarations.

Verify:
- target text does not influence scanner policy;
- descriptive metadata cannot downgrade structural risk;
- malformed MCP does not break OpenAPI/A2A.

---

# 8. Phase 2A — A2A Red Team

Create unseen Agent Cards:

- valid card;
- missing required field;
- invalid skill;
- duplicate skill ID;
- unsupported version;
- malformed auth metadata;
- deceptive capability description;
- conflicting capability declarations.

Verify failure isolation.

---

# 9. Capability Graph Consistency

Represent one semantic capability through:

```text
OpenAPI
MCP
A2A
```

Independently decide the expected canonical semantics first.

Then compare actual graph output.

Verify:
- action class;
- input schema;
- output schema;
- side-effect classification;
- auth requirements;
- protocol provenance.

Material inconsistency is a Phase 2A defect.

---

# 10. v1 Security Regression Audit

Independently verify:

1. raw artifact body absent from public reports;
2. credentials never leak;
3. `file://` rejected;
4. private-network SSRF blocked;
5. redirects revalidated;
6. evidence provenance correct;
7. mutation risk monotonic;
8. malformed advertised artifacts visible;
9. fatal scan failure nonzero exit;
10. target content cannot become instructions.

Create at least one fresh test for each where practical.

---

# 11. Ownership Verification Red Team

## DNS TXT

Test:
- correct token;
- wrong token;
- expired token;
- replayed token;
- token for parent domain;
- token for sibling subdomain;
- multiple TXT records;
- stale DNS behavior;
- wrong environment binding.

## HTTPS `.well-known`

Test:
- correct challenge;
- wrong challenge;
- expired challenge;
- redirect to another host;
- redirect to localhost;
- redirect to private IP;
- path normalization tricks;
- encoding tricks;
- same challenge copied to another domain.

Expected:

> Verification must be exact-target and environment scoped.

---

# 12. Agent Identity Red Team

Test:
- UNKNOWN;
- DECLARED;
- CRYPTOGRAPHICALLY_VERIFIED;
- PARTNER;
- INTERNAL;
- forged provider ID;
- duplicate agent ID;
- expired identity;
- wrong key ID;
- provider/agent mismatch.

Critical test:

> Can `CRYPTOGRAPHICALLY_VERIFIED` be constructed without actual cryptographic verification?

If yes, classify severity based on authorization impact.

---

# 13. HTTP Message Signature Testing

Required cases:
- valid signature;
- invalid signature;
- unknown key;
- wrong key ID;
- expired key;
- modified body;
- modified method;
- modified target URI;
- missing required signed component;
- old timestamp;
- future timestamp outside tolerance;
- duplicate nonce;
- replayed exact request;
- unsupported algorithm.

For state-changing requests:

> Signature failure must fail closed when verified identity is required.

---

# 14. Replay Protection Testing

Test:

```text
same signature
same nonce
same request
```

twice.

Second attempt MUST be rejected.

Also test:
- same nonce with changed body;
- same nonce from different agent;
- nonce after expiry;
- high-volume duplicate attempts.

Verify replay state is scoped appropriately.

---

# 15. Delegation Red Team

Test:
- valid grant;
- expired grant;
- not-yet-valid grant;
- revoked grant;
- wrong principal;
- wrong agent;
- wrong provider;
- wrong audience;
- wrong capability;
- wrong resource;
- exceeded value;
- wrong currency;
- wrong geography;
- insufficient scope;
- excessive scope.

Then test combinations.

One mandatory mismatch must deny.

---

# 16. Confused Deputy Tests

Mandatory:

### A
Agent A has valid grant. Agent B uses it.
Expected: `DENY`

### B
Same provider, wrong agent.
Expected: `DENY`

### C
Same agent, wrong principal.
Expected: `DENY`

### D
Capability A grant used for capability B.
Expected: `DENY`

### E
$100 grant used for $1,000.
Expected: `DENY`

### F
Resource X grant used for Y.
Expected: `DENY`

---

# 17. OAuth Assessment Testing

Determine whether implementation distinguishes:

```text
DECLARED OAuth support
```

from:

```text
VERIFIED authorization behavior
```

Test:
- valid metadata;
- malformed metadata;
- broad scopes;
- narrow scopes;
- missing audience;
- wrong audience;
- missing revocation support where expected;
- missing PKCE indication where applicable.

Do not assume OAuth presence means secure authorization.

---

# 18. Sender-Constrained Token / DPoP Testing

Where implemented:
- valid proof;
- wrong key;
- replayed proof;
- stale proof;
- wrong method;
- wrong URL;
- invalid nonce;
- token/proof key mismatch.

Where not supported:

Output should be `NOT_OBSERVED` or `UNSUPPORTED`, not PASS.

---

# 19. Policy Engine Red Team

Test:
- ALLOW;
- DENY;
- REQUIRE_HUMAN;
- ALLOW_WITH_LIMITS.

Create policies for:
- explicit DENY;
- broad ALLOW;
- narrow ALLOW;
- missing default;
- expired rule;
- future rule;
- conflicting rule;
- duplicate priority;
- wildcard capability;
- wildcard agent;
- stale version;
- no owner.

Critical question:

> Can broad ALLOW override specific DENY?

Expected: only if documented deterministic precedence explicitly permits it.

---

# 20. Policy Determinism

Run identical inputs repeatedly.

Compare normalized outputs.

Must remain identical for:
- decision;
- matched rule;
- reason;
- missing conditions;
- required next action.

---

# 21. Policy Explanation Integrity

Create denials caused by:
- value limit;
- wrong principal;
- missing confirmation;
- expired policy;
- unknown agent.

Verify the explanation cites the true cause.

Wrong explanations corrupt auditability.

---

# 22. Policy Version / Staleness

Scenario:

```text
policy v1 = ALLOW
policy v2 = DENY
```

Test:
- cached v1;
- new v2;
- concurrent requests;
- policy load failure;
- stale cache;
- rollback attempt.

State-changing execution must not silently continue under stale ALLOW.

---

# 23. Policy Audit Trail

Verify:
- updates create new version;
- old versions immutable;
- owner preserved;
- change event exists;
- evidence references exact version used;
- history cannot be silently overwritten.

---

# 24. State-Changing Fail-Closed Matrix

Create one synthetic mutation capability.

Test:

| Identity | Delegation | Policy | Integrity | Expected |
|---|---|---|---|---|
| missing | valid | allow | valid | DENY |
| valid | missing | allow | valid | DENY |
| valid | valid | missing | valid | DENY |
| valid | expired | allow | valid | DENY |
| valid | valid | error | valid | DENY |
| valid | valid | allow | invalid | DENY |
| valid | valid | allow | valid | ALLOW/controlled |

No failed security component may silently become ALLOW.

---

# 25. Secret / Logging Audit

Inject fake:
- access token;
- refresh token;
- bearer token;
- ownership challenge;
- signature;
- private-key-like text;
- sensitive principal identifier.

Search:
- CLI;
- JSON;
- Markdown;
- logs;
- exceptions;
- eval results;
- audit events;
- policy history.

No raw secret may leak.

---

# 26. Mutation Testing Audit

Run builder mutation harness.

Required mutations:

1. disable ownership verification;
2. bypass signature validation;
3. bypass replay;
4. accept expired grant;
5. ignore revocation;
6. ignore principal binding;
7. ignore audience binding;
8. ignore agent binding;
9. disable value check;
10. default allow;
11. ignore explicit DENY;
12. disable policy version check;
13. disable secret redaction.

Every critical mutation MUST trigger failures.

A surviving critical mutation is a HIGH/CRITICAL test weakness.

---

# 27. Independent Manual Mutation Sampling

Do not rely only on builder's mutation harness.

Manually disable at least three controls in a temporary audit copy.

Recommended:
- default deny;
- replay protection;
- principal binding.

Verify normal suite fails.

Restore the audit copy afterward.

---

# 28. Architecture Audit

Answer:

1. Is there one canonical production implementation?
2. Is `agentnative_v2` absent from production dependencies?
3. Is packaging clean?
4. Are v1 security controls preserved?
5. Are protocol adapters modular?
6. Is identity separate from delegation?
7. Is policy separate from both?
8. Can Phase 2C be added without rewriting Phase 2B?

---

# 29. False-Confidence Review

Look for overstatement such as:

```text
OAuth exists ≠ authorization verified
signature metadata exists ≠ signature verified
verified provider ≠ authorized action
valid protocol ≠ safe business operation
delegation object exists ≠ delegation proven
policy exists ≠ policy enforced
```

Classify each risk.

---

# 30. Finding Format

Every finding:

```yaml
finding_id:
severity:
title:
requirement:
component:
reproduction:
expected:
observed:
evidence:
impact:
release_gate_impact:
recommended_fix:
```

Severity:
`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`.

Do not report speculation as confirmed vulnerability.

---

# 31. Required Audit Artifacts

Create:

```text
audit_v2/INDEPENDENT_V2_AUDIT.md
audit_v2/REQUIREMENTS_RECONSTRUCTION.md
audit_v2/PHASE_2A_RESULTS.md
audit_v2/PHASE_2B_RESULTS.md
audit_v2/SECURITY_RED_TEAM.md
audit_v2/MUTATION_RESULTS.md
audit_v2/RELEASE_GATE_MATRIX.md
audit_v2/REMEDIATION_BACKLOG.md
audit_v2/findings.json
```

Do not modify production source.

---

# 32. Release Gate Matrix

For each major control use:

```text
PASS
FAIL
PARTIAL
NOT_VERIFIED
NOT_APPLICABLE
```

Required areas:

## Phase 2A
- OpenAPI JSON/YAML
- safe refs
- MCP
- A2A
- adapter isolation
- capability normalization
- provenance
- v1 invariants

## Phase 2B
- ownership
- identity
- signatures
- replay
- delegation
- OAuth assessment
- sender-constrained-token assessment
- confused-deputy prevention
- policy
- policy audit
- policy staleness
- fail-closed behavior
- secret safety
- mutation coverage

---

# 33. Final Response Format

## 1. Executive Verdict

```text
PHASE_2A: ...
PHASE_2B: ...
```

## 2. Independently Verified
Only reproduced claims.

## 3. Not Verified
Explicit limitations.

## 4. New Fixtures / Tests
List independent cases.

## 5. Architecture Findings
Root migration, duplication, boundaries.

## 6. Phase 2A Findings
Protocols and capability graph.

## 7. Phase 2B Findings
Ownership, identity, signatures, replay, delegation, policy.

## 8. Fail-Closed Results
State-changing authorization matrix.

## 9. Mutation Results
Builder harness plus manual independent mutations.

## 10. False-Confidence Risks
What the product might overclaim.

## 11. Release Gate Matrix
PASS/FAIL/PARTIAL/NOT_VERIFIED.

## 12. Remediation Backlog

Use:

```text
P0 — immediate
P1 — required before Phase 2B READY
P2 — required before Phase 2C
P3 — later hardening
```

## 13. Principal Engineer Review

Answer:
- What architecture is strong?
- What would a Staff/Principal interviewer challenge?
- What assumptions remain under-tested?
- What is the most important unresolved risk?

---

# 34. Final Rule

Do not repair the implementation during this audit.

AUDIT FIRST.

The builder will receive the remediation backlog afterward.

The audit succeeds when it discovers the truth—not when it produces a green verdict.

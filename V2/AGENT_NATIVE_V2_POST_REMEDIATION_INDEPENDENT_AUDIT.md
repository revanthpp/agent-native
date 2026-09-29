# Agent Native v2 — Post-Remediation Independent Audit Prompt

## Purpose

Run an independent verification of the remediated Agent Native v2 implementation before Phase 2C.

This is **not a build prompt**. Do **not** modify production code.

Current builder-reported state:

- canonical implementation under `src/agentnative/`
- duplicate `v2core` / incubation runtime removed
- complete adapter contract for OpenAPI, MCP, A2A
- safe same-origin remote `$ref` through `SafeFetcher`
- redirect, SSRF, cycle, depth, size, timeout, provenance protections
- all ten policy-linter rules implemented
- production-seam mutation testing reports `17/17 caught`
- Phase 2A eval corpus added
- clean-install docs and CI checks added
- wheel contents verified
- no legacy `v2core` or `agentnative_v2`
- semantic `agentnative policy lint`
- `pytest`: 77 passed, 144 subtests
- `unittest`: 77 passed
- `pip check`: clean
- installed-wheel CLI smoke passed

Current conservative release status:

```text
PHASE_2A_NOT_READY
PHASE_2B_CONDITIONALLY_READY
PHASE_2C_NOT_STARTED
```

The explicit reason for not promoting Phase 2A is that independent `audit_v2/` evidence has not yet been produced.

The BRD remains the source of truth.

---

# 1. Role

Act as an independent:

- Principal Agent Systems Architect
- Security Engineer
- Protocol Conformance Reviewer
- Identity / Authorization Reviewer
- QA / Evaluation Lead
- Release Gate Auditor

You did not build this code.

Do not trust builder claims, test counts, release-review conclusions, traceability statuses, comments, README language, or mutation counts without reproducing them.

Your job is to determine whether the implementation actually satisfies Phase 2A and Phase 2B.

---

# 2. Audit-only rule

Do NOT modify production source under:

```text
src/agentnative/
```

Do NOT repair defects.

You may create isolated audit assets only under:

```text
audit_v2/
```

You may use temporary worktrees, temporary copies, independent fixtures, local test servers, monkeypatches, and temporary mutation experiments.

---

# 3. Required source documents

Read:

```text
Agent_Native_v2_Product_BRD.md
AGENT_NATIVE_V2_INDEPENDENT_TEST.md
docs/evals/INDEPENDENT_AUDIT_RUNBOOK.md
docs/REQUIREMENTS_TRACEABILITY.md
PHASE_2A_RELEASE_REVIEW.md
PHASE_2B_RELEASE_REVIEW.md
docs/security/V2_THREAT_MODEL.md
```

If anything is missing, report it.

---

# 4. Required audit artifacts

Create:

```text
audit_v2/
  INDEPENDENT_V2_AUDIT.md
  REQUIREMENTS_RECONSTRUCTION.md
  CLEAN_ENVIRONMENT_RESULTS.md
  ARCHITECTURE_RESULTS.md
  PHASE_2A_RESULTS.md
  PHASE_2B_RESULTS.md
  PROTOCOL_ADAPTER_RESULTS.md
  REMOTE_REF_RESULTS.md
  POLICY_LINT_RESULTS.md
  SECURITY_RED_TEAM.md
  MUTATION_RESULTS.md
  PACKAGE_RESULTS.md
  RELEASE_GATE_MATRIX.md
  REMEDIATION_BACKLOG.md
  findings.json
```

Do not write PASS conclusions before executing the underlying checks.

---

# 5. Reconstruct requirements independently

Before trusting repository traceability, reconstruct Phase 2A and Phase 2B requirements directly from the BRD.

For each:

```yaml
requirement_id:
phase:
mandatory:
expected_component:
expected_behavior:
release_gate:
```

Classify as:

```text
MANDATORY
SHOULD
OPTIONAL
DEFERRED_TO_2C
DEFERRED_TO_V3
```

Then compare against `docs/REQUIREMENTS_TRACEABILITY.md`.

Report:

- missing requirements
- incorrect phase assignment
- missing production references
- missing tests/evals
- false VERIFIED claims
- implementation missing from traceability

---

# 6. Canonical architecture audit

Verify:

1. canonical implementation is under `src/agentnative/`
2. no production `v2core.py` remains authoritative
3. no production package named `agentnative_v2` is shipped
4. no production imports depend on `agentnative_v2`
5. protocol logic is not duplicated
6. tests exercise canonical modules
7. wheel contains one intended runtime package
8. CLI resolves to canonical root package

Search for:

```text
v2core
agentnative_v2
v2/src
compatibility bridge
```

Classify hits as:

```text
PRODUCTION
TEST
HISTORICAL_DOC
PROMPT
ARCHIVE
```

Answer:

> If an engineer fixes OpenAPI `$ref` behavior, is there exactly one obvious production module to change?

Repeat for MCP, A2A, identity, delegation, and policy.

---

# 7. Clean environment reproduction

Perform both:

## Editable clean install

```bash
python -m venv .audit-env
source .audit-env/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest
```

Use repository-equivalent commands where necessary.

## Built wheel

Build a wheel, create a second clean environment, install the wheel plus declared test/audit dependencies, then run CLI smoke tests.

Verify at minimum:

```text
agentnative --help
agentnative scan --help
agentnative protocols --help
agentnative capabilities --help
agentnative owner --help
agentnative policy --help
```

Record exact commands and results.

Any mandatory skipped test blocks READY.

---

# 8. Protocol adapter contract audit

The BRD requires behavior equivalent to:

```text
detect
parse
validate
normalize
enumerate_capabilities
enumerate_auth_requirements
enumerate_actions
enumerate_errors
enumerate_protocol_limitations
```

Verify each is:

- present in the common adapter contract
- available for OpenAPI
- available for MCP
- available for A2A
- exercised by tests
- implemented in canonical production modules

Create a matrix:

| Adapter | detect | parse | validate | normalize | capabilities | auth | actions | errors | limitations |
|---|---|---|---|---|---|---|---|---|---|

Do not accept thin re-exports as implementation evidence.

---

# 9. Extension SDK audit

Create a NEW test-only `IndependentDummyAdapter`.

Register it without changing built-in adapter source.

Prove:

```text
registration
detection
parse
validation
normalization
enumeration
failure isolation
```

If a new adapter requires modifying a hardcoded production switch, the extension requirement is not satisfied.

---

# 10. OpenAPI audit

Create unseen fixtures for:

- JSON
- YAML
- malformed YAML
- malicious YAML object tags
- supported 3.x version
- unsupported version
- malformed schema
- operation extraction
- auth extraction
- errors / limitations
- canonical capability normalization

---

# 11. Same-origin remote `$ref` red team

This was a previous blocker. Test independently.

Required cases:

1. valid local ref
2. valid same-origin remote ref
3. nested same-origin ref
4. safe same-origin redirect
5. redirect to different origin
6. redirect to localhost/private network
7. localhost ref
8. RFC1918 ref
9. link-local ref
10. cloud metadata address
11. IPv6 loopback/private
12. `file://`
13. unsupported scheme
14. recursive ref
15. multi-document cycle
16. max depth
17. max document count
18. 404
19. timeout
20. oversized body
21. malformed remote document
22. nested-ref provenance

Verify:

- all acquisition passes through the security boundary
- redirects are revalidated
- blocked refs do not cause unsafe fetches
- referenced artifacts retain correct provenance
- failed refs do not fabricate capability evidence

---

# 12. MCP audit

Create unseen fixtures for:

- valid tool/resource/prompt surface
- declared capabilities
- auth requirements
- malformed input/output schemas
- duplicate IDs
- unknown extensions
- deceptive descriptions
- destructive tool claiming read-only
- prompt-injection text
- unsupported version/profile

Verify:

- conformance is distinct from trust
- natural language cannot downgrade structural risk
- failures remain isolated
- normalization preserves provenance

---

# 13. A2A audit

Create unseen Agent Cards for:

- valid card
- missing required fields
- duplicate skill ID
- malformed skill
- auth declaration
- unsupported version
- conflicting declarations
- deceptive descriptions

Verify parse, validate, normalize, inventory, auth, errors, limitations, and failure isolation.

A2A compatibility must not imply trusted identity.

---

# 14. Cross-protocol capability normalization

Independently define one capability first, for example:

```yaml
name: create_reservation
action_class: CREATE
side_effect: REVERSIBLE
authentication_required: true
confirmation_required: false
```

Represent it through OpenAPI, MCP, and A2A.

Verify semantic consistency while preserving protocol-specific provenance.

---

# 15. Policy linter audit

Independently test all ten required linter rules:

1. missing default
2. unowned rule
3. expired rule
4. future-rule ambiguity
5. wildcard privilege
6. contradictory rules
7. unreachable rule
8. sensitive action without required confirmation
9. duplicate ambiguity
10. environment inconsistency

For each create:

- one case that MUST trigger
- one safe case that MUST NOT trigger

Also test:

```bash
agentnative policy lint <fixture>
```

Verify semantics, not just exit code.

---

# 16. Policy precedence / fail-closed audit

Test:

```text
specific DENY vs broad ALLOW
```

Also test:

- equal-priority contradiction
- expired DENY
- future ALLOW
- environment-specific rule
- wildcard rule
- missing default
- unknown state-changing capability

State-changing behavior without an applicable allow must DENY.

---

# 17. Identity, signature, replay audit

Create unseen cases for:

- valid Ed25519 signature
- invalid signature
- wrong key
- wrong agent/key binding
- modified method
- modified URI
- modified body/content digest
- stale timestamp
- future timestamp
- duplicate nonce
- replayed exact request

Critical invariant:

> `CRYPTOGRAPHICALLY_VERIFIED` can only result from successful cryptographic verification.

Attempt alternate construction/promotion paths.

---

# 18. OAuth / DPoP evidence audit

Verify result semantics distinguish:

```text
DECLARED
OBSERVED
VERIFIED
NOT_OBSERVED
UNSUPPORTED
INVALID
```

Test representative cases for:

- OAuth metadata only
- valid metadata
- malformed metadata
- declared DPoP
- observed proof without full verification
- valid proof where supported
- wrong key
- wrong method
- wrong URI
- stale proof
- replay
- token/proof mismatch where applicable

Critical invariant:

```text
DECLARED != VERIFIED
```

---

# 19. Delegation / confused deputy audit

Test:

- valid grant
- expired
- revoked
- wrong principal
- wrong agent
- wrong provider
- wrong audience
- wrong capability
- wrong resource
- excessive value
- geography mismatch
- insufficient scope
- excessive scope

Mandatory confused-deputy cases:

```text
Agent B uses Agent A grant -> DENY
Capability B uses Capability A grant -> DENY
Resource Y uses Resource X grant -> DENY
$100 grant used for $1,000 -> DENY
```

---

# 20. State-changing fail-closed matrix

Use one synthetic mutation capability.

| Identity | Integrity | Delegation | Policy | Expected |
|---|---|---|---|---|
| missing | n/a | valid | allow | DENY |
| valid | invalid | valid | allow | DENY |
| valid | valid | missing | allow | DENY |
| valid | valid | expired | allow | DENY |
| valid | valid | valid | missing | DENY |
| valid | valid | valid | error | DENY |
| valid | valid | valid | DENY | DENY |
| valid | valid | valid | ALLOW | ALLOW/controlled |

A security-component error must never silently become ALLOW.

---

# 21. Audit the 17/17 mutation claim

Inspect every builder mutation.

For each record:

```yaml
mutation_id:
claimed_control:
actual_production_target:
mutation_method:
expected_failure:
actual_failed_tests:
restoration_verified:
meaningful:
```

Reject as evidence:

- toy helper mutations
- duplicated fake security logic
- mutation-only code disconnected from runtime
- predetermined lambdas that do not replace the real production seam

A mutation counts only if it disables or alters canonical production behavior.

---

# 22. Independently reproduce at least five mutations

In a temporary worktree/copy, independently defeat at least:

1. state-changing default DENY
2. replay protection
3. delegation principal binding
4. unsafe remote `$ref` restriction
5. secret redaction

Run the normal suite.

Each defect should cause relevant tests to fail.

If a critical mutation survives, report HIGH/CRITICAL evaluation weakness.

Restore state after each experiment.

---

# 23. Secret / evidence audit

Inject fake:

- bearer/access/refresh tokens
- private-key-like strings
- signatures
- DPoP proofs
- ownership challenges
- sensitive principal identifiers

Inspect:

- CLI
- JSON
- Markdown
- logs
- exceptions
- eval output
- audit records

No raw secret may leak.

---

# 24. v1 security regression audit

Independently verify:

1. no raw artifact body in public report
2. no credential leakage
3. `file://` rejected
4. private-network SSRF blocked
5. redirects revalidated
6. evidence provenance correct
7. mutation risk not downgradable by target metadata
8. malformed artifact remains observable
9. fatal execution nonzero
10. target content remains data

Use fresh tests where practical.

---

# 25. Release-evidence integrity audit

For at least ten mandatory requirements, manually walk:

```text
BRD
→ traceability
→ architecture
→ source
→ test
→ eval
→ release review
```

Document broken links.

This step specifically prevents release evidence from getting ahead of implementation again.

---

# 26. Findings format

Severity:

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
phase:
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

Do not report speculation as a confirmed vulnerability.

---

# 27. Phase 2A gate

`PHASE_2A_READY` requires:

- canonical architecture verified
- full adapter contract verified
- OpenAPI verified
- safe same-origin remote refs verified
- MCP contract verified
- A2A contract verified
- extension seam independently demonstrated
- cross-protocol normalization verified
- provenance verified
- truthful traceability
- clean install + wheel execution
- no mandatory skips
- no HIGH/CRITICAL unresolved Phase 2A finding

Choose exactly one:

```text
PHASE_2A_READY
PHASE_2A_CONDITIONALLY_READY
PHASE_2A_NOT_READY
```

---

# 28. Phase 2B gate

`PHASE_2B_READY` requires:

- Phase 2A READY
- ownership verification passes
- cryptographic identity passes
- signature/replay protections pass
- delegation bindings pass
- confused-deputy cases deny
- OAuth/DPoP evidence semantics are honest
- policy precedence/fail-closed behavior passes
- all ten linter rules pass
- policy version/audit/staleness behavior passes
- mutation coverage is production-sensitive
- independent critical mutations are caught
- secret/evidence safety passes
- no HIGH/CRITICAL unresolved Phase 2B finding

Choose exactly one:

```text
PHASE_2B_READY
PHASE_2B_CONDITIONALLY_READY
PHASE_2B_NOT_READY
```

---

# 29. Do not start Phase 2C

Regardless of verdict:

DO NOT implement Phase 2C.

If both gates are READY, say:

```text
Phase 2A and Phase 2B are independently release-ready.
Proceed to the Phase 2C build directive in a separate development cycle.
```

Otherwise produce remediation backlog.

---

# 30. Final response format

## 1. Executive Verdict
`PHASE_2A: ...`
`PHASE_2B: ...`

## 2. Clean Environment Results
Exact commands and outcomes.

## 3. Canonical Architecture
Duplication / package findings.

## 4. Requirements / Traceability Integrity
Broken or complete evidence chains.

## 5. Protocol Adapter Results
OpenAPI / MCP / A2A / extension seam.

## 6. Remote `$ref` Results
Safety and provenance.

## 7. Policy Linter Results
All ten rules.

## 8. Identity / Delegation / Policy Results
Including fail-closed matrix.

## 9. Mutation Results
Builder harness plus independent mutation sampling.

## 10. v1 Regression Results
All ten invariants.

## 11. Findings
Grouped by severity.

## 12. Release Gate Matrix
Use PASS / FAIL / PARTIAL / NOT_VERIFIED / NOT_APPLICABLE.

## 13. Remediation Backlog
- P0 — immediate blocker
- P1 — required before READY
- P2 — required before Phase 2C
- P3 — later hardening

## 14. Principal Engineer Review
Answer:
- What is architecturally strong?
- What remains provisional?
- Has release-evidence drift been structurally addressed?
- What would a Staff/Principal reviewer challenge next?

## 15. Next Action
If both READY: proceed to Phase 2C in a separate cycle.
Otherwise: remediate P0/P1 and rerun this audit.

---

# Final Rule

The goal is not to validate the builder.

The goal is to establish the truth.

A release gate is valuable only when a different reviewer can reproduce the evidence without trusting the person or model that built it.

Begin the independent audit now.

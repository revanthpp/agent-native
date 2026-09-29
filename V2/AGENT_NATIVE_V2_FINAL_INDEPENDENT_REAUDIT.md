# Agent Native v2 — Final Independent Re-Audit Prompt
## Close the prior adapter-boundary finding and make the Phase 2A / Phase 2B release decision

## Purpose

Run the **final independent re-audit** of Agent Native v2 after the targeted adapter-boundary remediation.

This is an audit-only task.

Do NOT modify production code.

The previous independent audit concluded:

```text
PHASE_2A_CONDITIONALLY_READY
PHASE_2B_CONDITIONALLY_READY
PHASE_2C_NOT_STARTED
```

The remaining finding was:

> Direct `OpenAPIAdapter.detect()` / `.parse()` calls could leak a PyYAML `ConstructorError` for hostile YAML tags instead of returning a structured Agent Native error result.

The remediation builder now reports:

- OpenAPI direct calls safely normalize malicious/malformed YAML;
- structured `AdapterError` includes evidence and provenance;
- registry and direct adapter classifications are consistent;
- MCP/A2A malformed-input boundaries were reviewed;
- sanitized CLI rendering was added;
- a production-seam mutation `M-ADAPTER-YAML-ERROR` was added;
- traceability and threat model were updated;
- `pytest`: 84 passed, 158 subtests;
- `unittest`: 84 passed;
- `pip check`: clean;
- wheel verification passed;
- installed CLI smoke passed;
- mutation harness: 18/18 caught;
- prior `audit_v2/` evidence was not modified;
- Phase 2C has not started.

Your job is to independently verify these claims and make the final Phase 2A / Phase 2B release-gate decision.

---

# 1. Role

Act as an independent:

- Principal Agent Systems Architect
- Security Engineer
- Protocol Conformance Reviewer
- QA / Evaluation Lead
- Release Gate Auditor

You did NOT build the remediation.

Do not trust:

- builder-written tests;
- builder conclusions;
- reported test counts;
- release-review labels;
- traceability status;
- mutation counts.

Reproduce the evidence.

---

# 2. Absolute audit rule

Do NOT modify:

```text
src/agentnative/
tests/
evals/
docs/
```

except for creating isolated audit evidence under a new directory.

Do not repair defects.

Do not change expected results.

Create a new audit iteration:

```text
audit_v2/rerun_01/
```

Do NOT overwrite the original independent audit.

---

# 3. Required inputs

Read:

```text
Agent_Native_v2_Product_BRD.md
audit_v2/INDEPENDENT_V2_AUDIT.md
audit_v2/findings.json
audit_v2/REMEDIATION_BACKLOG.md
audit_v2/RELEASE_GATE_MATRIX.md

docs/remediation/OPENAPI_ADAPTER_ERROR_BOUNDARY_FIX.md
docs/REQUIREMENTS_TRACEABILITY.md
docs/security/V2_THREAT_MODEL.md

PHASE_2A_RELEASE_REVIEW.md
PHASE_2B_RELEASE_REVIEW.md
```

Also inspect the canonical implementation and builder tests directly.

---

# 4. Required outputs

Create:

```text
audit_v2/rerun_01/
  FINAL_REAUDIT.md
  OPENAPI_ADAPTER_BOUNDARY_RETEST.md
  CROSS_ADAPTER_BOUNDARY_RETEST.md
  MUTATION_RETEST.md
  CLEAN_ENVIRONMENT_RETEST.md
  PHASE_2A_RELEASE_GATE.md
  PHASE_2B_RELEASE_GATE.md
  RELEASE_GATE_MATRIX.md
  findings.json
  REMEDIATION_BACKLOG.md
```

If no remediation remains, `REMEDIATION_BACKLOG.md` should explicitly state that no P0/P1 release blockers remain.

---

# 5. First priority — retest the exact prior finding

Before running broad suites, independently reproduce the original defect class.

Use new hostile YAML fixtures not copied from builder tests.

At minimum test:

```yaml
!!python/object/apply:os.system ["echo audit-test"]
```

plus separate examples using:

```text
!!python/object/new
!!python/name
unknown custom YAML tag
malformed YAML syntax
```

Test direct public OpenAPI adapter paths.

At minimum:

```text
detect()
parse()
```

and any other public operation that may independently parse/inspect target-controlled YAML.

Expected:

- no code execution;
- no raw PyYAML `ConstructorError` escaping;
- structured Agent Native error/invalid result;
- sanitized message;
- artifact/source provenance retained;
- no raw hostile payload reflected unsafely.

---

# 6. Direct adapter vs registry consistency

For every hostile YAML fixture, execute through:

```text
direct OpenAPIAdapter path
```

and:

```text
AdapterRegistry path
```

Verify substantive classification is consistent.

The exact wrapper structure may differ, but this is unacceptable:

```text
direct adapter → uncaught exception
registry       → structured invalid
```

Also verify the opposite does not occur:

```text
direct adapter → invalid
registry       → false valid
```

Record actual results.

---

# 7. Unexpected internal error separation

The remediation must not have solved the problem using an overly broad:

```python
except Exception:
    return INVALID
```

that hides implementation defects.

Inspect the error boundary.

Verify expected target-input failures are normalized, while genuine unexpected internal/programming failures remain distinguishable as internal adapter errors or are propagated according to the documented internal-error contract.

Create one controlled audit case if practical to ensure an unrelated programming-style exception is not mislabeled as ordinary invalid YAML.

The goal is:

```text
hostile target input
→ structured target-input failure

internal implementation defect
→ distinguishable internal failure
```

---

# 8. Provenance on invalid artifacts

Verify hostile/malformed artifacts retain appropriate evidence such as:

- artifact identifier;
- source URI where safe;
- content hash where the project uses it;
- acquisition provenance;
- adapter/protocol identity.

Malformed input must not disappear merely because parsing failed.

---

# 9. CLI/report sanitization

Run the relevant CLI/report path on malicious YAML.

Verify:

- no stack trace exposed as normal output;
- no unsafe raw target-controlled payload reflected;
- no secret-like content leaked;
- useful structured failure remains visible.

---

# 10. Cross-adapter boundary retest

The prior finding exposed a **defect class**, not merely a YAML bug.

Independently test malformed direct calls against:

## MCP
- wrong top-level type;
- malformed tool schema;
- malformed auth field;
- unexpected nested structure.

## A2A
- wrong top-level type;
- malformed Agent Card;
- malformed skill;
- malformed auth declaration.

Expected:

> Normal hostile/invalid target inputs do not leak third-party parser/validator exceptions from the public adapter boundary.

If an adapter has no third-party parser, still verify deterministic structured domain errors.

---

# 11. Retest mutation `M-ADAPTER-YAML-ERROR`

Inspect the new mutation.

Verify that it targets the canonical production error-normalization seam.

Reject it if it mutates:

- a test-only helper;
- duplicate logic;
- an unused wrapper;
- a fake mutation-specific implementation.

Run the mutation.

Expected:

- the new hostile-YAML boundary tests fail;
- the harness reports the mutation caught;
- source state is restored.

---

# 12. Independent manual mutation

Do not rely solely on the builder harness.

In a temporary audit copy/worktree:

1. disable the adapter-level YAML error normalization;
2. restore behavior where the underlying `ConstructorError` escapes;
3. run the relevant normal tests.

Expected:

```text
tests fail
```

Restore state after the experiment.

Record exact tests that detect the defect.

---

# 13. Clean environment rerun

From a new clean environment:

```bash
python -m venv .audit-rerun-env
source .audit-rerun-env/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest
```

Then independently run the unittest path if the repository supports both.

Record:

```text
passed
failed
skipped
subtests
warnings
```

Mandatory skips block READY.

---

# 14. Wheel / installed-artifact rerun

Build a fresh wheel.

Install it into another clean environment.

Verify:

- no `agentnative_v2`;
- no legacy `v2core`;
- canonical imports resolve;
- CLI smoke passes;
- malicious OpenAPI YAML through the installed package still fails safely.

This final malicious-YAML installed-wheel check is mandatory.

It proves the fix exists in the distributable artifact, not only the working tree.

---

# 15. Full mutation harness rerun

Run all production mutations.

Expected builder claim:

```text
18/18 caught
```

Independently inspect that all 18 remain meaningful production-seam mutations.

At minimum confirm coverage for:

- ownership;
- signature;
- replay;
- delegation;
- explicit DENY;
- default deny;
- policy version/staleness;
- redaction;
- unsafe `$ref`;
- adapter YAML error boundary.

Do not certify the count if any mutation is disconnected from runtime.

---

# 16. Phase 2A regression spot checks

Even though this is a targeted re-audit, independently spot-check prior high-risk Phase 2A areas:

- full adapter contract;
- same-origin remote `$ref`;
- unsafe redirect blocking;
- MCP malformed input;
- A2A malformed input;
- extension adapter registration;
- cross-protocol capability normalization;
- provenance.

You do not need to reinvent the entire previous audit if prior evidence remains valid and code affecting those areas did not change.

However, rerun any test whose dependency path changed during remediation.

---

# 17. Phase 2B regression spot checks

Independently spot-check:

- cryptographic identity promotion;
- signature verification;
- replay;
- delegation principal/agent/audience binding;
- confused deputy;
- explicit DENY precedence;
- state-changing default deny;
- policy lint;
- DPoP/OAuth evidence semantics.

Again, rerun more broadly if the remediation touched shared models or error handling used by these components.

---

# 18. Traceability integrity

Review the updated traceability for the original finding.

Verify the chain exists:

```text
BRD requirement / adapter invariant
→ canonical OpenAPI adapter
→ structured error model
→ regression test
→ mutation
→ threat model
→ release gate
```

No nonexistent paths.

No inflated status.

---

# 19. Threat-model integrity

Verify the threat model now covers the defect class:

> malformed/hostile protocol artifact escapes parser-specific exception across adapter boundary.

Required defense-in-depth concept:

```text
safe parser
+
adapter-level normalization
+
registry isolation
```

The registry must not be the only error boundary.

---

# 20. Findings severity

Use:

```text
CRITICAL
HIGH
MEDIUM
LOW
INFO
```

Every new finding:

```yaml
finding_id:
severity:
title:
phase:
component:
reproduction:
expected:
actual:
evidence:
release_gate_impact:
recommended_remediation:
```

Do not treat theoretical concerns as reproduced vulnerabilities.

---

# 21. Phase 2A final gate

Choose exactly one:

```text
PHASE_2A_READY
PHASE_2A_CONDITIONALLY_READY
PHASE_2A_NOT_READY
```

READY requires:

- previous open adapter-boundary finding independently closed;
- no replacement HIGH/CRITICAL Phase 2A finding;
- canonical architecture remains valid;
- protocol adapter contract remains valid;
- remote `$ref` protections remain valid;
- clean environment succeeds;
- installed wheel succeeds;
- mandatory tests have zero skips;
- evidence chain is accurate.

---

# 22. Phase 2B final gate

Choose exactly one:

```text
PHASE_2B_READY
PHASE_2B_CONDITIONALLY_READY
PHASE_2B_NOT_READY
```

READY requires:

- Phase 2A READY;
- no HIGH/CRITICAL Phase 2B finding;
- critical identity/delegation/policy regressions remain green;
- production mutation evidence remains meaningful;
- adapter remediation did not weaken reporting/redaction/fail-closed behavior.

---

# 23. Phase 2C remains forbidden during audit

Do NOT implement Phase 2C.

If both final gates are READY, report:

```text
PHASE_2A_READY
PHASE_2B_READY

Independent Phase 2A / Phase 2B verification is complete.
Phase 2C may begin in a separate development cycle.
```

That is the stopping point.

---

# 24. Final report format

## 1. Final Verdict

```text
PHASE_2A: ...
PHASE_2B: ...
```

## 2. Prior Finding Retest
Was the raw `ConstructorError` defect independently closed?

## 3. Error Boundary Quality
Does the adapter distinguish hostile input from internal implementation errors?

## 4. Direct vs Registry Consistency
Results.

## 5. MCP / A2A Boundary Review
Results.

## 6. Mutation Retest
`M-ADAPTER-YAML-ERROR`, independent manual mutation, full harness.

## 7. Clean Environment
Exact commands and results.

## 8. Installed Wheel
Package and malicious-input result.

## 9. Phase 2A Regression
Spot-check matrix.

## 10. Phase 2B Regression
Spot-check matrix.

## 11. Traceability / Threat Model
Integrity results.

## 12. New Findings
Grouped by severity.

## 13. Release Gate Matrix
Use PASS / FAIL / PARTIAL / NOT_VERIFIED.

## 14. Remaining Remediation
P0 / P1 / P2 / P3.

## 15. Principal Engineer Assessment
Answer:
- Is the prior defect class actually closed?
- Is the adapter contract now defensible for hostile input?
- Is evidence still ahead of implementation anywhere?
- Is the system ready to introduce controlled action in Phase 2C?

## 16. Next Action
If both READY:

```text
Begin Phase 2C using the approved Phase 2C build directive.
```

Otherwise:

```text
Remediate P0/P1 findings and rerun this audit.
```

---

# Final Rule

Do not reward the builder for adding a test.

Verify the architectural invariant:

> **Every protocol adapter is safe at its own public boundary when consuming hostile target-controlled input.**

If that invariant is independently proven, and no other release blocker emerges, close Phase 2A and Phase 2B.

Then stop.

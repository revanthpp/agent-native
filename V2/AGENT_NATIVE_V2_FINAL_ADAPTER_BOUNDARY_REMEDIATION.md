# Agent Native v2 — Final Phase 2A / 2B Closure Remediation
## Close the adapter error-boundary defect, re-run independent verification, and stop before Phase 2C

## Purpose

This is a **targeted final remediation**, not another broad feature sprint.

Independent post-remediation audit reported:

```text
PHASE_2A_CONDITIONALLY_READY
PHASE_2B_CONDITIONALLY_READY
PHASE_2C_NOT_STARTED
```

The audit independently reproduced:

- clean editable install;
- `pip check`;
- `pytest`: 77 passed, 144 subtests;
- `unittest`: 77 OK;
- wheel build/install;
- CLI smoke;
- package verification;
- production-seam mutation harness: 17/17 caught.

The remaining reported finding is:

> Direct `OpenAPIAdapter.detect()` / `.parse()` calls can leak a PyYAML `ConstructorError` for malicious YAML tags instead of returning a structured Agent Native invalid/error result.

The registry catches the exception safely, but the adapter boundary itself does not.

This matters because protocol adapters consume **untrusted target-controlled artifacts**. Their safety contract must hold whether invoked through the registry or directly.

The goal of this sprint is to fix the **defect class**, not merely the exact test fixture.

Do NOT start Phase 2C.

---

# 1. Authoritative Inputs

Read before changing code:

```text
Agent_Native_v2_Product_BRD.md
audit_v2/INDEPENDENT_V2_AUDIT.md
audit_v2/findings.json
audit_v2/REMEDIATION_BACKLOG.md
audit_v2/RELEASE_GATE_MATRIX.md
audit_v2/PHASE_2A_RESULTS.md
audit_v2/PHASE_2B_RESULTS.md
docs/REQUIREMENTS_TRACEABILITY.md
```

The BRD remains the product source of truth.

The independent audit evidence is the source of truth for the currently open defect.

---

# 2. Role

Act as Principal Engineer and Security Architect responsible for closing the final Phase 2A defect without weakening the adapter contract or release gates.

Do not:

- alter the independent audit verdict manually;
- edit `audit_v2/` evidence to turn it green;
- suppress the failing behavior with a broad catch-all;
- make malicious YAML "valid";
- downgrade the BRD requirement;
- begin Phase 2C.

---

# 3. Root Cause to Address

The observed symptom is:

```text
malicious / unsupported YAML tag
        ↓
PyYAML parser
        ↓
yaml.constructor.ConstructorError
        ↓
raw library exception escapes direct OpenAPIAdapter API
```

The registry currently catches the exception.

That is insufficient.

The architectural defect is:

> **The safety/error-normalization boundary exists at the registry layer but not at the protocol-adapter boundary.**

The correct invariant is:

> **Every protocol adapter must safely consume untrusted target-controlled input when invoked directly or through the registry. Expected target-input failures must be normalized into Agent Native domain results, not leaked as parser/library-specific exceptions.**

---

# 4. Required Adapter Error Contract

Inspect the current canonical adapter interface before changing signatures.

Use the smallest change that makes the contract coherent across adapters.

The resulting contract MUST distinguish at least:

```text
VALID
VALID_WITH_WARNINGS
INVALID
UNSUPPORTED
NOT_DETECTED
ERROR
```

or the equivalent statuses already defined by the canonical implementation.

For target-controlled malformed/unsafe input:

```text
raw parser exception
```

MUST become:

```text
structured Agent Native error / invalid result
```

containing at minimum:

```yaml
status:
error_code:
message:
protocol:
artifact_reference:
sanitized_details:
```

Do not expose:

- raw secret-bearing artifact content;
- Python stack traces in public result objects;
- parser implementation internals unnecessarily.

---

# 5. Exception Taxonomy

Do NOT add:

```python
except Exception:
    return INVALID
```

as the primary solution.

Instead classify expected failures.

For OpenAPI parsing, explicitly handle expected target-input exceptions such as:

```text
yaml.YAMLError / ConstructorError family
JSON decode errors
expected schema-validation errors
expected reference-resolution errors
```

Map them to Agent Native domain errors.

Unexpected programming/runtime defects should remain distinguishable as internal errors rather than silently being reclassified as invalid target input.

Recommended conceptual separation:

```text
TARGET_INPUT_INVALID
TARGET_INPUT_UNSUPPORTED
SECURITY_POLICY_BLOCKED
ADAPTER_INTERNAL_ERROR
```

Use existing project terminology if equivalent types already exist.

---

# 6. OpenAPI Direct-Call Safety

Direct calls to all public OpenAPI adapter operations MUST behave safely on hostile input.

At minimum verify:

```text
detect()
parse()
validate()
normalize()
enumerate_capabilities()
enumerate_auth_requirements()
enumerate_actions()
enumerate_errors()
enumerate_protocol_limitations()
```

where applicable to the current interface.

A malformed artifact MUST NOT cause a parser-specific exception to escape during normal target-input handling.

If later methods require a successfully parsed object, they must:

- return an explicit structured error/invalid result; or
- accept only a typed successful parse result and reject invalid states through the documented domain contract.

Do not leave ambiguous mixed semantics.

---

# 7. Malicious YAML Cases

Add canonical production tests for more than the exact independent-audit fixture.

At minimum test:

```yaml
!!python/object/apply:os.system ["echo unsafe"]
```

and representative unsupported/unsafe YAML tags such as:

```text
!!python/object/new
!!python/name
unknown custom tag
```

Also retain cases for:

- malformed YAML syntax;
- ordinary valid YAML;
- valid OpenAPI YAML.

Expected:

- no object construction;
- no code execution;
- no raw `ConstructorError` leakage;
- structured invalid/error semantics;
- no regression for valid YAML.

---

# 8. Direct vs Registry Consistency

For the same malicious artifact, compare:

```text
direct OpenAPIAdapter invocation
```

with:

```text
AdapterRegistry invocation
```

The two paths MUST agree on the substantive classification.

They do not need identical wrapper objects, but they MUST NOT produce:

```text
direct → uncaught exception
registry → structured invalid
```

after remediation.

Add an explicit regression test.

---

# 9. Cross-Adapter Boundary Review

The YAML finding exposes an adapter-boundary defect class.

Do a narrow review of MCP and A2A direct APIs for the same class.

Create malformed/adversarial direct-call inputs for:

## MCP
- malformed schema;
- unexpected type;
- invalid declared structure;
- oversized/hostile text where existing limits apply.

## A2A
- malformed Agent Card;
- unexpected types;
- missing required structures;
- invalid version/profile input.

Expected:

> Expected target-input failures are normalized through the adapter contract and do not leak library-specific parser/validator exceptions.

Do NOT add unrelated new protocol features.

---

# 10. Structured Error Requirements

Each normalized adapter error SHOULD contain enough information for:

- debugging;
- evidence;
- release reporting;

without exposing sensitive raw data.

Recommended fields:

```yaml
code: OPENAPI_YAML_PARSE_INVALID
category: TARGET_INPUT_INVALID
protocol: openapi
operation: parse
message: YAML document could not be safely parsed
artifact_id: ...
source_uri: ...
```

If the existing error model differs, preserve the canonical model rather than creating parallel types.

Avoid exposing raw exception strings when they could contain target-controlled data.

---

# 11. Evidence / Provenance

A parsing failure is still evidence.

The error result MUST retain:

- artifact identity;
- source URI where safe;
- content hash where already used by the project;
- acquisition provenance;
- adapter/version information.

Do not let malformed artifacts disappear.

This preserves the existing Agent Native invariant:

> lack of parse success does not erase evidence that an advertised artifact existed.

---

# 12. Required Tests

Add targeted tests such as:

```text
tests/protocols/test_openapi_error_boundary.py
```

or the closest canonical location.

Required assertions:

1. valid JSON remains valid;
2. valid YAML remains valid;
3. malformed YAML returns structured invalid/error;
4. malicious YAML tag returns structured invalid/error;
5. malicious YAML tag does not execute;
6. raw `ConstructorError` does not escape;
7. direct adapter and registry classification are consistent;
8. error retains provenance;
9. public rendering sanitizes error details;
10. MCP direct malformed input does not leak expected parser errors;
11. A2A direct malformed input does not leak expected parser errors.

---

# 13. Add a Defect-Class Regression Test

Do not only test one exception type.

Add a parameterized or equivalent test asserting:

> **Expected target-controlled parsing/validation failures never escape canonical protocol adapters as third-party library exceptions.**

The test should enumerate known expected exception families rather than catching arbitrary programming defects.

This is the regression that prevents the architecture from drifting back to registry-only safety.

---

# 14. Mutation Test for the New Boundary

Extend the real production mutation harness.

Add a mutation that disables the OpenAPI adapter's expected YAML error normalization so that `ConstructorError` escapes again.

The normal test suite MUST catch the mutation.

Example conceptual mutation:

```text
production_target:
  OpenAPI adapter safe YAML parse boundary

mutation:
  bypass domain-error conversion and invoke parser directly

expected:
  direct-adapter hostile-YAML regression test fails
```

The mutation MUST target canonical production code.

---

# 15. Traceability Update

Update:

```text
docs/REQUIREMENTS_TRACEABILITY.md
```

Map the relevant adapter/error-handling requirements to:

```text
canonical adapter
→ error model
→ direct-call regression tests
→ registry consistency test
→ mutation test
→ independent audit gate
```

Do not alter Phase 2A to READY yet.

Builder-side status remains non-final until the independent audit is rerun.

---

# 16. Threat Model Update

Update:

```text
docs/security/V2_THREAT_MODEL.md
```

Add or refine the threat:

```text
Malformed / hostile protocol artifact causes parser-specific exception to escape adapter boundary
```

Map:

```text
Threat
→ safe parser
→ adapter-level error normalization
→ registry isolation
→ direct-call regression test
→ mutation test
→ residual risk
```

The point is defense in depth:

```text
Safe parser
+
Adapter boundary
+
Registry boundary
```

not registry-only exception containment.

---

# 17. Builder Verification

After implementation run:

```text
targeted new tests
full pytest
full unittest
pip check
package build
wheel verification
installed-wheel CLI smoke
17 existing production-seam mutations
new adapter-error mutation
v1 regressions
Phase 2A regressions
Phase 2B regressions
```

Mandatory tests must have zero skips.

Record exact counts.

---

# 18. Do Not Rewrite Independent Audit Evidence

Do NOT edit existing:

```text
audit_v2/findings.json
audit_v2/RELEASE_GATE_MATRIX.md
audit_v2/INDEPENDENT_V2_AUDIT.md
```

to mark the issue fixed.

Those files describe the prior audit run.

Instead create a builder remediation record:

```text
docs/remediation/OPENAPI_ADAPTER_ERROR_BOUNDARY_FIX.md
```

Include:

```yaml
finding:
root_cause:
production_fix:
tests_added:
mutation_added:
builder_verification:
ready_for_reaudit: true|false
```

---

# 19. Builder Gate

After the fix, the builder may report:

```text
READY_FOR_INDEPENDENT_REAUDIT
```

but MUST NOT self-promote the independent release verdict.

Do not change:

```text
PHASE_2A_CONDITIONALLY_READY
PHASE_2B_CONDITIONALLY_READY
```

to final READY solely from builder evidence.

The independent auditor must close the finding.

---

# 20. Independent Re-Audit Handoff

If builder verification passes, stop and provide this exact next action:

```text
Re-run the post-remediation independent audit with a different model,
focusing first on the previously open OpenAPIAdapter error-boundary finding,
then rerun the Phase 2A and Phase 2B release gate matrices.
```

The auditor should create a NEW audit iteration, for example:

```text
audit_v2/rerun_01/
```

or version the existing audit artifacts clearly.

Do not overwrite the prior evidence.

---

# 21. Expected Final Sequence

```text
Current independent audit
    ↓
1 open adapter-boundary finding
    ↓
THIS TARGETED REMEDIATION
    ↓
builder full regression
    ↓
READY_FOR_INDEPENDENT_REAUDIT
    ↓
different model re-audits
    ↓
PHASE_2A_READY
PHASE_2B_READY
    ↓
ONLY THEN:
Phase 2C
```

---

# 22. Required Final Builder Response

Report:

## 1. ROOT CAUSE
Why the raw `ConstructorError` escaped.

## 2. ARCHITECTURE FIX
Where the adapter-level safety boundary now lives.

## 3. ERROR CONTRACT
Exact domain result/status used.

## 4. OPENAPI TESTS
Valid, malformed, malicious-tag, direct/registry consistency.

## 5. CROSS-ADAPTER REVIEW
MCP/A2A direct-call safety result.

## 6. MUTATION TEST
New production mutation and whether suite catches it.

## 7. REGRESSION RESULTS
Full counts and skipped count.

## 8. PACKAGE / CLI RESULTS
Wheel and installed artifact verification.

## 9. TRACEABILITY / THREAT MODEL
Files updated.

## 10. STATUS

Use:

```text
READY_FOR_INDEPENDENT_REAUDIT
```

or:

```text
REMEDIATION_NOT_READY
```

Do not start Phase 2C.

---

# Final Engineering Rule

The lesson from this finding is bigger than YAML.

A registry catching exceptions is not the same as an adapter having a safe contract.

Agent Native treats every target artifact as hostile.

Therefore:

> **Safety must exist at the component boundary where hostile data first becomes domain behavior — not only at the outer orchestration layer.**

Fix the boundary.

Prove it directly.

Mutation-test it.

Then let an independent reviewer close the gate.

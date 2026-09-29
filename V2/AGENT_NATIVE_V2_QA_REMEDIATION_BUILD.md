# Agent Native v2 — Phase 2A/2B QA Remediation Build Directive
## Re-ground the implementation in the BRD before Phase 2C

**Status entering this remediation:**<br>
`PHASE_2A_NOT_READY`<br>
`PHASE_2B_CONDITIONALLY_READY`

**Primary objective:**<br>
Bring the implementation, tests, traceability, and release evidence back into alignment with the Agent Native v2 BRD.

**Do not begin Phase 2C until this remediation is complete and independently re-tested.**

---

# 1. Why this remediation exists

Independent QA found that the implementation is directionally promising, but the release evidence is ahead of the code.

The important issue is not simply that some tests are missing.

The deeper issue is:

> **The repository currently claims architectural capabilities that are not fully represented by the canonical implementation.**

That creates false confidence.

The remediation therefore MUST fix both:

1. the implementation gaps; and
2. the evidence/traceability gaps that allowed those gaps to be marked complete.

The goal is not to make the QA report green.

The goal is to make the architecture, implementation, tests, and release claims describe the same system.

---

# 2. Independent QA findings to remediate

The following findings are treated as authoritative inputs for this sprint.

## QA-V2-001 — Traceability points to missing implementation/tests

The traceability file claims Phase 2A implementation through paths such as:

```text
protocols/openapi/adapter.py
tests/protocols/test_openapi.py
```

but the canonical root implementation is concentrated in:

```text
src/agentnative/v2core.py
```

with thin re-export modules.

This makes traceability unreliable.

### Defect class

```text
Release evidence drift
+
documentation-to-code divergence
```

### Required outcome

Every traceability claim MUST point to an existing:

```text
requirement
→ architecture component
→ production file
→ test
→ eval
→ release gate
```

No missing path may be marked `IMPLEMENTED` or `VERIFIED`.

---

## QA-V2-002 — Protocol adapter contract is incomplete

The BRD requires protocol adapters to support:

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

The current base abstraction reportedly exposes only:

```text
detect
parse
```

MCP and A2A currently behave primarily as declared-surface analyzers rather than full conformance adapters.

### Defect class

```text
Architecture contract not implemented
```

### Required outcome

Phase 2A adapters MUST implement the BRD-defined common interface and be independently testable.

---

## QA-V2-003 — Safe remote `$ref` support is incomplete

The BRD requires approved same-origin remote `$ref` resolution through the network policy.

The current implementation reportedly returns a limitation for all non-local refs.

### Defect class

```text
Mandatory capability deferred without changing release gate
```

### Required outcome

Either:

1. implement safe same-origin remote `$ref` resolution according to the BRD; or
2. if the BRD is intentionally changed, update the BRD through an explicit product decision/ADR before changing the release gate.

For this remediation, default to option 1.

Do NOT weaken the requirement merely to preserve the current implementation.

---

## QA-V2-004 — Mutation evidence is not control-sensitive

The current mutation script reportedly labels many controls but applies the same baseline behavior and does not mutate real ownership, signature, replay, delegation, redaction, or policy-version production paths.

### Defect class

```text
Evaluation theater / false-positive mutation coverage
```

### Required outcome

The mutation harness MUST disable or alter the actual production controls and prove the normal test suite detects the defect.

---

## QA-V2-005 — Independent test directive has not been executed reproducibly

The independent test plan exists, but there is no `audit_v2/` evidence, and the current environment lacked `pytest` and `cryptography`.

### Defect class

```text
Unproven release reproducibility
```

### Required outcome

A clean environment MUST be able to install the product and test dependencies and execute the required audit.

The build must distinguish:

```text
runtime dependencies
development/test dependencies
```

The final evidence must include actual `audit_v2/` outputs from a different model or independent audit run.

---

## QA-V2-006 — Policy linting is incomplete

The BRD requires linting for:

- unreachable rules;
- contradictions;
- wildcard privilege;
- missing default;
- expired rules;
- rules without owner;
- high-risk actions without confirmation.

Current implementation reportedly covers only part of this.

### Defect class

```text
Partial implementation represented as complete
```

### Required outcome

Implement every mandatory linter behavior from the BRD and test each independently.

---

# 3. Release status reset

Before coding, update release artifacts so they reflect current truth.

Phase 2A MUST be represented as:

```text
PHASE_2A_NOT_READY
```

until the Phase 2A blockers in this document are independently closed.

Phase 2B MUST remain:

```text
PHASE_2B_CONDITIONALLY_READY
```

because Phase 2B currently depends on a Phase 2A foundation that has not been proven release-ready.

Do not retain stale `READY` labels in current release documents.

Historical files MAY retain prior decisions if clearly labeled as historical.

---

# 4. Remediation order

Execute in this order:

```text
A. Evidence / traceability reset
B. Canonical architecture cleanup
C. Protocol adapter contract
D. OpenAPI remote $ref
E. Phase 2A protocol/conformance tests
F. Policy linter completion
G. Real mutation harness
H. Clean environment / test reproducibility
I. Full Phase 2A + 2B regression
J. Independent audit
```

Do NOT start Phase 2C.

---

# 5. A — Rebuild requirements traceability from reality

Create or rewrite:

```text
docs/REQUIREMENTS_TRACEABILITY.md
```

Do not copy old statuses forward automatically.

For every Phase 2A and Phase 2B requirement include:

| Requirement | Mandatory? | Architecture | Production file(s) | Tests | Eval | Status | Evidence |
|---|---|---|---|---|---|---|---|

Allowed statuses:

```text
NOT_STARTED
PARTIAL
IMPLEMENTED
VERIFIED
DEFERRED_BY_BRD
BLOCKED
```

Rules:

- `IMPLEMENTED` requires production code.
- `VERIFIED` requires passing tests/evals against canonical production code.
- missing files cannot be referenced;
- historical/incubation paths cannot count as canonical implementation;
- thin re-export modules MUST NOT be cited as implementation if logic lives elsewhere;
- one test cannot be cited for unrelated controls.

Create:

```text
docs/remediation/V2_QA_TRACEABILITY_REPAIR.md
```

For each QA finding map:

```text
Finding
→ Root cause
→ BRD requirement
→ Architecture fix
→ Code
→ Regression test
→ Eval
→ Release gate
```

---

# 6. B — Canonical architecture cleanup

The current concentration of v2 behavior in:

```text
src/agentnative/v2core.py
```

is not automatically wrong, but it creates two problems:

1. it obscures component boundaries;
2. it makes traceability and independent testing harder.

Refactor Phase 2A/2B logic into coherent modules matching the BRD architecture.

Target structure:

```text
src/agentnative/
  protocols/
    base.py
    registry.py
    openapi/
      adapter.py
      parser.py
      refs.py
      models.py
    mcp/
      adapter.py
      models.py
    a2a/
      adapter.py
      models.py

  capabilities/
    models.py
    graph.py
    normalization.py

  ownership/
    models.py
    verifier.py

  identity/
    models.py
    signatures.py
    replay.py
    dpop.py

  delegation/
    models.py
    verifier.py
    oauth.py

  policy/
    models.py
    engine.py
    lint.py
    audit.py

  security/
  evidence/
  reporting/
```

You MAY choose slightly different filenames if justified.

Requirements:

- one canonical implementation;
- no duplicated business logic;
- re-export modules may exist for compatibility but must not hide alternate implementations;
- tests must import canonical modules;
- release traceability must point to canonical modules.

Create ADR if this refactor materially changes module boundaries.

---

# 7. C — Implement the complete Protocol Adapter contract

Create a common abstract interface/protocol.

Minimum required operations:

```python
detect(...)
parse(...)
validate(...)
normalize(...)
enumerate_capabilities(...)
enumerate_auth_requirements(...)
enumerate_actions(...)
enumerate_errors(...)
enumerate_protocol_limitations(...)
```

The exact Python signatures may differ, but behavior MUST be explicit.

Every adapter must return typed results.

Suggested adapter result model:

```yaml
protocol_family:
protocol_version:
adapter_version:
detected:
validity:
capabilities:
auth_requirements:
actions:
errors:
limitations:
evidence_refs:
```

Validity states:

```text
VALID
VALID_WITH_WARNINGS
INVALID
UNSUPPORTED
NOT_DETECTED
```

---

# 8. Adapter invariants

All adapters MUST satisfy:

1. malformed input cannot crash unrelated adapters;
2. unsupported features become explicit limitations;
3. protocol text is treated as data;
4. adapters cannot alter security policy;
5. target metadata cannot lower structural risk;
6. every normalized capability retains protocol provenance;
7. adapter errors are distinguishable from target readiness findings;
8. protocol version is explicit;
9. adapter version is explicit.

---

# 9. OpenAPI adapter requirements

The OpenAPI adapter MUST support Phase 2A BRD scope including:

- JSON;
- YAML;
- supported OpenAPI 3.x versions as documented;
- validation;
- capability extraction;
- auth extraction;
- action enumeration;
- error/limitation reporting;
- safe `$ref` resolution.

Tests MUST call adapter methods directly as well as through end-to-end flows.

---

# 10. D — Implement safe same-origin remote `$ref`

Remote `$ref` is mandatory for Phase 2A READY according to the current BRD.

Implement safe resolution under the same outbound network policy used elsewhere.

Required rules:

## Allowed

```text
same-origin HTTPS references
```

subject to network policy.

## Blocked

```text
file://
localhost
loopback
RFC1918/private IP
link-local
cloud metadata
reserved ranges
unsupported schemes
```

Cross-origin references MUST follow explicit BRD policy.

If cross-origin is not supported, return a specific limitation.

---

# 11. `$ref` safety controls

Implement:

- maximum reference depth;
- maximum referenced document count;
- cycle detection;
- canonical URI resolution;
- redirect revalidation;
- response-size limits;
- timeout;
- provenance preservation;
- deterministic failure semantics.

A remote referenced artifact MUST have its own:

```text
artifact_id
source_uri
content_hash
acquisition evidence
```

Do not attribute referenced evidence to the root OpenAPI artifact incorrectly.

---

# 12. `$ref` adversarial tests

Create new tests for:

1. valid local ref;
2. valid same-origin remote ref;
3. remote ref redirecting same-origin safely;
4. remote ref redirecting to localhost;
5. private IP ref;
6. metadata IP ref;
7. `file://`;
8. unsupported scheme;
9. recursive ref;
10. multi-file cycle;
11. max depth exceeded;
12. max document count exceeded;
13. remote 404;
14. timeout;
15. oversized referenced document;
16. malformed referenced document;
17. provenance across nested refs.

A blocked unsafe ref MUST NOT result in any unsafe fetch attempt.

---

# 13. MCP adapter completion

The MCP adapter must not be merely a metadata reader.

Within the passive/conformance boundary, implement:

- protocol detection;
- parsing;
- validation;
- capability inventory;
- tool/action inventory;
- auth requirement extraction;
- error collection;
- limitation collection;
- normalization into capability graph.

Do NOT execute MCP tools during passive Phase 2A assessment.

Active invocation remains later.

Add conformance-oriented fixtures for:

- valid declared surface;
- malformed schema;
- duplicate tool IDs;
- missing required fields;
- unsupported extension;
- deceptive description;
- destructive tool labeled read-only;
- prompt-injection text.

---

# 14. A2A adapter completion

Implement:

- Agent Card detection;
- parsing;
- validation;
- skill/capability inventory;
- auth requirements;
- actions;
- errors;
- limitations;
- capability normalization.

A2A compatibility MUST NOT imply trust.

Fixtures:

- valid Agent Card;
- missing required fields;
- duplicate skill ID;
- malformed auth;
- unsupported version;
- conflicting declaration;
- deceptive description.

---

# 15. Extension SDK proof

The BRD requires an adapter extension seam.

Prove this by creating one minimal test-only adapter outside the built-in protocol packages.

Example:

```text
DummyProtocolAdapter
```

It MUST be registerable without modifying:

```text
OpenAPIAdapter
MCPAdapter
A2AAdapter
```

Test:

```text
register
detect
parse
validate
normalize
enumerate...
```

This is the proof that the architecture is extensible rather than a hardcoded switch statement.

---

# 16. Capability normalization proof

Create one synthetic business capability represented through:

```text
OpenAPI
MCP
A2A
```

Example semantic capability:

```text
create_reservation
```

Independently define canonical expected semantics:

```yaml
action_class: CREATE
side_effect: REVERSIBLE
requires_auth: true
requires_confirmation: false
```

Then prove all three adapters normalize into semantically equivalent capability graph entries while preserving:

```text
protocol source
artifact source
protocol-specific identifier
evidence
```

Material differences must be explicit.

---

# 17. E — Phase 2A test suite reconstruction

Create real test locations aligned with traceability.

Recommended:

```text
tests/protocols/test_adapter_contract.py
tests/protocols/test_openapi.py
tests/protocols/test_openapi_refs.py
tests/protocols/test_mcp.py
tests/protocols/test_a2a.py
tests/protocols/test_extension_sdk.py
tests/capabilities/test_normalization.py
tests/security/test_protocol_boundaries.py
```

Do not create empty test files merely to satisfy traceability.

Tests must exercise actual behavior.

---

# 18. Phase 2A eval corpus

Create:

```text
evals/phase2a/
```

Include unseen-style fixtures covering:

- valid;
- invalid;
- ambiguous;
- unsupported;
- adversarial;
- deceptive.

Create a manifest:

```text
evals/phase2a/manifest.json
```

Each eval record:

```yaml
eval_id:
requirement:
protocol:
fixture:
expected:
release_blocking:
rationale:
```

---

# 19. Phase 2A release gate

Phase 2A may become READY only if:

- complete adapter contract implemented;
- OpenAPI adapter fulfills contract;
- MCP adapter fulfills contract;
- A2A adapter fulfills contract;
- extension SDK demonstrated;
- same-origin remote `$ref` supported safely;
- all required `$ref` safety cases pass;
- capability normalization demonstrated;
- provenance verified;
- traceability points to real files/tests/evals;
- no mandatory tests skipped;
- no high/critical unresolved Phase 2A defect.

Update:

```text
PHASE_2A_RELEASE_REVIEW.md
```

Status exactly:

```text
PHASE_2A_READY
PHASE_2A_CONDITIONALLY_READY
PHASE_2A_NOT_READY
```

---

# 20. F — Complete Policy Linter

Implement all BRD-required lint checks.

At minimum:

## POL-LINT-001 — Missing default
Policy set has no explicit default behavior.

## POL-LINT-002 — Unowned rule
Rule has no owner.

## POL-LINT-003 — Expired rule
Rule is expired but still active/present.

## POL-LINT-004 — Future rule ambiguity
Rule effective date is future but configuration treats it as active.

## POL-LINT-005 — Wildcard privilege
Broad wildcard grants sensitive/state-changing capabilities.

## POL-LINT-006 — Contradictory rules
Same effective match space leads to incompatible decisions.

## POL-LINT-007 — Unreachable rule
Higher-precedence rule completely shadows another rule.

## POL-LINT-008 — Sensitive action without confirmation
High-risk capability can be permitted with no required confirmation where configured policy requires such a control.

## POL-LINT-009 — Duplicate ambiguity
Duplicate match keys/priority cause ambiguous interpretation.

## POL-LINT-010 — Environment inconsistency
Production policy accidentally includes sandbox-only behavior or equivalent invalid targeting.

---

# 21. Policy precedence proof

Document deterministic precedence.

Test at minimum:

```text
specific DENY
vs
broad ALLOW
```

Expected result MUST follow documented precedence.

Test:

- same priority contradiction;
- explicit deny;
- wildcard allow;
- expired deny;
- future allow;
- environment-specific rule.

---

# 22. Policy lint tests

Create:

```text
tests/policy/test_lint.py
```

Each required lint rule needs:

- positive trigger case;
- negative safe case.

Do not combine all linter behavior into one opaque test.

---

# 23. G — Replace mutation theater with real mutation testing

The current reported `16/16 caught` evidence is invalid for release purposes because it does not mutate production controls.

Retire or rewrite the current mutation harness.

A mutation MUST alter real production behavior.

---

# 24. Required production mutations

At minimum:

1. ownership verification always returns true;
2. signature verification always returns valid;
3. replay store accepts duplicate nonce;
4. delegation expiry ignored;
5. revocation ignored;
6. principal binding ignored;
7. agent binding ignored;
8. audience binding ignored;
9. capability binding ignored;
10. resource binding ignored;
11. value ceiling ignored;
12. explicit DENY ignored;
13. default DENY changed to ALLOW;
14. policy version/staleness bypassed;
15. secret redaction bypassed;
16. unsafe `$ref` network policy bypassed.

Every mutation MUST target canonical production code.

---

# 25. Mutation harness implementation options

Preferred approaches:

```text
temporary Git worktree
temporary source copy
controlled dependency-injection seam
test-time monkeypatch of production function
```

Whichever is chosen:

- identify exact source/function mutated;
- run the relevant real tests;
- restore state;
- fail if restoration fails;
- return nonzero if required mutation survives.

Output example:

```yaml
mutation_id: MUT-POL-DEFAULT-001
control: state-changing default deny
production_target: agentnative.policy.engine.PolicyEngine.evaluate
mutation: return ALLOW when no rule matches
expected_failures:
  - tests/policy/test_engine.py::test_state_change_without_rule_denied
caught: true
```

---

# 26. Mutation acceptance gate

100% of release-critical mutations MUST be caught.

Do not use:

```text
16/16
```

as evidence unless all 16 mutate real production controls.

A surviving mutation is a release blocker.

---

# 27. H — Clean environment reproducibility

Add explicit development/test dependency configuration.

Recommended pattern:

```toml
[project.optional-dependencies]
dev = [
  "pytest>=...",
  ...
]
```

Runtime dependencies such as `cryptography` and YAML parser remain normal runtime dependencies if required by product behavior.

A clean verification flow MUST work:

```bash
python -m venv .venv-audit
source .venv-audit/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest
```

Use equivalent Windows commands where relevant.

Document in:

```text
CONTRIBUTING.md
docs/evals/RUNNING_TESTS.md
```

---

# 28. Clean package verification

Also verify built artifact, not only editable install:

```text
build wheel
create fresh environment
install wheel + test/audit dependencies
run installed CLI smoke
run selected black-box tests
```

This detects source-tree import accidents.

---

# 29. I — Execute the independent audit directive

Once builder remediation passes locally, execute the independent test plan.

Create actual:

```text
audit_v2/
```

containing:

```text
INDEPENDENT_V2_AUDIT.md
REQUIREMENTS_RECONSTRUCTION.md
PHASE_2A_RESULTS.md
PHASE_2B_RESULTS.md
SECURITY_RED_TEAM.md
MUTATION_RESULTS.md
RELEASE_GATE_MATRIX.md
REMEDIATION_BACKLOG.md
findings.json
```

These outputs MUST come from the independent audit process.

The builder MUST NOT fabricate them.

The builder MAY prepare the repository so the other model can run them.

---

# 30. Phase 2B re-verification after Phase 2A repair

Because Phase 2B depends on Phase 2A capability semantics, rerun:

- ownership;
- signatures;
- replay;
- identity promotion;
- delegation;
- OAuth evidence classification;
- DPoP assessment;
- policy evaluation;
- policy lint;
- policy versioning/audit;
- fail-closed matrix;
- secret safety;
- real production mutations.

---

# 31. Phase 2B gate

Phase 2B can only be `READY` when:

- Phase 2A is `READY`;
- clean environment tests execute;
- production mutation harness is real and passes;
- policy lint meets BRD;
- no critical/high unresolved defect;
- independent audit evidence exists;
- current traceability is truthful.

---

# 32. Do not start Phase 2C

After the builder reaches:

```text
PHASE_2A_READY
PHASE_2B_READY
```

STOP.

The next action is:

```text
run independent red-team audit
```

If the independent audit also returns READY:

then Phase 2C may begin.

---

# 33. Required final builder report

Report exactly:

## 1. QA Finding Closure

Table:

| Finding | Status | Root cause | Fix | Test | Evidence |
|---|---|---|---|---|---|

Include QA-V2-001 through QA-V2-006.

## 2. Canonical Architecture

Show final module tree and explain removal/refactor of `v2core.py` responsibilities.

## 3. Adapter Contract

Show which class/module implements every required adapter method.

## 4. Remote `$ref`

Show same-origin behavior and security controls.

## 5. Policy Lint

List every linter rule and test.

## 6. Mutation Harness

List actual production targets mutated and failures caught.

## 7. Environment Reproducibility

Show clean install commands and results.

## 8. Test Results

Counts by category, including skipped tests.

## 9. Eval Results

Counts by category.

## 10. v1 Regression Results

All critical invariants.

## 11. Phase 2A Gate

Exactly one:

```text
PHASE_2A_READY
PHASE_2A_CONDITIONALLY_READY
PHASE_2A_NOT_READY
```

## 12. Phase 2B Gate

Exactly one:

```text
PHASE_2B_READY
PHASE_2B_CONDITIONALLY_READY
PHASE_2B_NOT_READY
```

## 13. Remaining Risks

Explicit residual risks only.

## 14. Next Action

If both READY:

```text
Run AGENT_NATIVE_V2_INDEPENDENT_TEST.md with a different model.
Do not start Phase 2C yet.
```

---

# 34. Final engineering rule

The central failure discovered by QA is:

> **The release artifacts described a more mature architecture than the code actually implemented.**

Do not repair that by changing wording alone.

Repair it by making all four layers converge:

```text
BRD
  ↓
Architecture
  ↓
Implementation
  ↓
Evidence
```

A requirement is not complete because it appears in a traceability table.

A security control is not proven because a mutation script prints `caught`.

A protocol is not supported because metadata can be parsed.

A release is ready only when the implementation and independent evidence justify the claim.

Finish Phase 2A correctly.

Then prove Phase 2B on top of it.

Then stop for independent verification.

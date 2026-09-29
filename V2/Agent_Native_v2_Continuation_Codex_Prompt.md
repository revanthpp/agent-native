# Agent Native v2 — Continuation Implementation Prompt for Codex

## Purpose

Continue development of Agent Native v2 from the current `PHASE_2A_CONDITIONALLY_READY` state.

This prompt is the execution directive for the next development cycle.

You have access to:

- the existing `agent-native` repository;
- `Agent_Native_v2_Product_BRD.md`;
- the current `/v2` implementation;
- existing v1 release artifacts;
- current Phase 2A tests/evals and release notes.

The BRD is the authoritative product source of truth.

Your objectives are:

1. close the remaining Phase 2A blocker;
2. migrate the v2 implementation from the temporary `/v2` incubation folder into the correct long-term repository root on a dedicated v2 development branch;
3. preserve the released v1 baseline through Git history/tagging rather than permanent duplicate source trees;
4. independently re-verify Phase 2A after migration;
5. implement Phase 2B:
   - business ownership verification;
   - agent identity;
   - delegated authorization;
   - participation policy engine;
6. add comprehensive tests, adversarial evals, and mutation tests;
7. stop before Phase 2C unless Phase 2B is independently ready.

Do not skip phase gates.

---

# 1. Current State

Reported Phase 2A status:

- BRD review complete;
- reuse matrix complete;
- gap analysis complete;
- architecture complete;
- threat model complete;
- ADRs complete;
- requirements traceability complete;
- protocol adapter interface complete;
- failure-isolated adapter registry complete;
- OpenAPI 3.x JSON/YAML support implemented;
- bounded safe `$ref` handling implemented;
- MCP adapter targeting revision `2026-07-28`;
- A2A adapter targeting `1.0.0`;
- canonical capability graph implemented;
- provenance and monotonic risk merging implemented;
- reference business fixtures implemented;
- Phase 2A eval manifest implemented;
- CLI prototype implemented.

Verification reported:

- v2: 10 tests passed;
- 1 mandatory YAML test skipped because PyYAML was not installed locally;
- v1: 50 existing tests passed;
- Python compilation passed;
- current gate: `PHASE_2A_CONDITIONALLY_READY`.

Treat this state as provisional until independently reproduced.

---

# 2. Repository Versioning Strategy

The `/v2` directory was an intentional incubation environment.

It MUST NOT remain the permanent product structure.

The long-term repository model should use Git versions and branches rather than nested product folders.

Desired model:

```text
v1.0.0 Git tag
    └── released v1 product

main
    └── current released version

develop/v2
    └── active v2 development at repository root

v2.0.0 Git tag
    └── created only after final v2 release
```

The active v2 product should eventually live at repository root:

```text
src/
  agentnative/

tests/
evals/
docs/
examples/

pyproject.toml
README.md
SECURITY.md
CONTRIBUTING.md
CHANGELOG.md
```

NOT permanently under:

```text
v2/src/
v2/tests/
v2/docs/
```

---

# 3. Git Safety Rules

Before restructuring:

1. inspect `git status`;
2. inspect current branch;
3. confirm whether tag `v1.0.0` exists;
4. identify exact v1 release commit;
5. preserve all historical release artifacts;
6. work on a dedicated branch such as:

```text
develop/v2
```

or equivalent.

Do NOT modify released history.

Do NOT force-push or rewrite tags.

If branch creation or Git state cannot be safely confirmed in the environment:

STOP.

Report the exact shell commands required for manual execution.

---

# 4. First Mandatory Task — Close YAML Dependency Gap

Phase 2A cannot be marked READY while a mandatory YAML test is skipped.

Investigate:

```text
v2/pyproject.toml
runtime dependencies
test dependencies
optional dependencies
CI install flow
clean-environment installation
```

If YAML is mandatory v2 functionality, its parser dependency MUST be installed as a normal runtime dependency unless there is a documented architectural reason otherwise.

Do NOT:

- keep the test skipped;
- make YAML optional merely to pass the gate;
- change the BRD;
- remove the test;
- weaken expected behavior.

Fix the dependency model.

Then verify in a clean environment.

Example:

```bash
python -m venv .tmp-v2-verify
source .tmp-v2-verify/bin/activate
python -m pip install -e .
python -m pytest
```

or the repository's equivalent test command.

Required outcome:

```text
0 skipped mandatory Phase 2A tests
```

---

# 5. Phase 2A Independent Re-Verification

Before migration, rerun and independently verify Phase 2A.

## OpenAPI

Test:

- JSON OpenAPI;
- YAML OpenAPI;
- malformed YAML;
- local `$ref`;
- same-origin remote `$ref`;
- recursive `$ref`;
- cyclic `$ref`;
- excessive `$ref` depth;
- private-network `$ref`;
- localhost `$ref`;
- cloud metadata `$ref`;
- `file://` `$ref`;
- missing reference;
- reference provenance;
- adapter failure isolation.

## MCP

Test:

- supported revision detection;
- tools;
- resources;
- prompts;
- auth metadata;
- malformed schemas;
- deceptive tool descriptions;
- destructive tool declared read-only;
- unknown extension;
- excessive schema size;
- adapter failure isolation.

## A2A

Test:

- Agent Card parsing;
- required fields;
- capability/skill normalization;
- malformed Agent Card;
- authentication declaration;
- unsupported features;
- adapter failure isolation.

## Capability Graph

Prove one equivalent business capability represented through:

```text
OpenAPI
MCP
A2A
```

normalizes into semantically equivalent capability objects while preserving protocol-specific provenance.

If outputs materially disagree:

STOP.

Resolve the abstraction before proceeding.

---

# 6. Migration Planning

Before moving files create:

```text
docs/migration/V2_ROOT_MIGRATION_PLAN.md
```

Include:

1. current v1 root structure;
2. current `/v2` structure;
3. v2 source files to promote;
4. v1 components to preserve;
5. v1 components to wrap;
6. components to merge;
7. components to replace;
8. tests/evals migration;
9. documentation migration;
10. dependency migration;
11. CLI migration;
12. CI migration;
13. rollback plan.

Also create:

```text
docs/migration/V1_TO_V2_COMPONENT_MATRIX.md
```

For every material component classify:

```text
KEEP
REUSE
WRAP
MERGE
REPLACE
REMOVE_AFTER_MIGRATION
```

At minimum review:

- v1 SafeFetcher;
- NetworkPolicy;
- sanitizer;
- public-report boundary;
- evidence model;
- secret detection;
- OpenAPI parser;
- existing check catalog;
- CLI;
- CI;
- fixtures;
- eval harness;
- threat model.

Do not discard hardened v1 security code without explicit justification.

---

# 7. Root Migration Principle

The migration goal is:

```text
v1 hardened foundations
        +
v2 architecture
        ↓
clean v2 root product
```

NOT:

```text
blindly copy /v2 over root
```

Perform:

```text
COPY / MERGE
→ TEST
→ VERIFY
→ REMOVE DUPLICATE
```

Never:

```text
DELETE FIRST
→ HOPE
```

---

# 8. Package Namespace

After migration, the canonical Python package SHOULD be:

```text
agentnative
```

not permanently:

```text
agentnative_v2
```

Preferred import style:

```python
from agentnative.protocols import ...
from agentnative.policy import ...
```

The product version belongs in package metadata.

If a temporary namespace is required during migration, document:

- why;
- where;
- how it will be removed;
- target release milestone.

---

# 9. CLI Strategy

Long-term CLI:

```bash
agentnative
```

not:

```bash
agentnative-v2
```

Target commands:

```bash
agentnative assess <target>
agentnative protocols <target>
agentnative capabilities <target>

agentnative owner verify <target>
agentnative owner status <target>

agentnative policy lint <policy-file>
agentnative policy evaluate <policy-file> <scenario>

agentnative simulate <target> --scenario <scenario>
agentnative simulate <target> --scenario <scenario> --dry-run

agentnative receipts verify <receipt>
```

Preserve the v1 command where practical:

```bash
agentnative scan ...
```

This may remain an alias or compatibility command.

Document behavior.

---

# 10. Documentation Strategy

After migration there must be one obvious current architecture.

Use root docs for active v2.

Historical v1 docs should remain accessible via:

- Git tag;
- `docs/history/v1/`;
- or equivalent archival structure.

Do not leave multiple source-of-truth files claiming different current architectures.

The v2 BRD remains authoritative.

---

# 11. CI Migration

Create/update v2-aware CI.

The pipeline MUST test current v2 and preserve critical v1 invariants.

Required categories:

```text
formatting
lint
typing
unit
integration
protocol
security
adversarial
eval
packaging
clean install
CLI smoke
```

During migration, retain either:

- full v1 regression tests;
- or a justified critical-invariant suite.

Do not reduce v1 protection before v2 parity is proven.

---

# 12. Critical v1 Security Invariants

Migration is NOT complete until all remain true.

1. no raw artifact body in public reports;
2. no credential leakage;
3. no `file://` network scanning;
4. no successful private-network SSRF;
5. redirect destinations are revalidated;
6. evidence provenance is validated;
7. target metadata cannot downgrade mutation risk;
8. malformed advertised artifacts remain visible;
9. scanner execution failures return nonzero exit status;
10. target content cannot act as instructions.

Create explicit regression tests if necessary.

---

# 13. Post-Migration Gate

After root migration:

Run:

- all v2 tests;
- all v2 evals;
- packaging;
- clean install;
- critical v1 security regressions.

Update:

```text
PHASE_2A_RELEASE_REVIEW.md
```

Final Phase 2A status must be exactly one:

```text
PHASE_2A_READY
PHASE_2A_CONDITIONALLY_READY
PHASE_2A_NOT_READY
```

Proceed only if:

```text
PHASE_2A_READY
```

---

# 14. Phase 2B — Business Ownership Verification

Once Phase 2A is READY, implement ownership verification.

Required methods:

1. DNS TXT challenge;
2. HTTPS `.well-known` challenge.

Create a model such as:

```yaml
verification_id:
business_id:
target:
method:
challenge_hash:
verified_at:
expires_at:
environment:
status:
```

Environment values:

```text
SANDBOX
STAGING
PRODUCTION_READ_ONLY
PRODUCTION_ACTIVE
```

Rules:

- active testing requires valid ownership verification;
- verification is exact-target scoped;
- verification expires;
- one hostname does not automatically verify another;
- challenge material cannot be reused indefinitely;
- production destructive execution remains disabled by default.

---

# 15. Ownership Threat Cases

Test:

- valid DNS challenge;
- invalid DNS challenge;
- stale DNS challenge;
- replayed challenge;
- wrong hostname;
- subdomain confusion;
- valid HTTPS challenge;
- redirected HTTPS challenge;
- expired ownership verification;
- verification removed after issuance;
- challenge endpoint compromised;
- same business attempting to use one verification on another domain.

Every ownership verification result needs evidence.

---

# 16. Agent Identity

Implement:

```yaml
agent_id:
provider_id:
display_name:
trust_class:
identity_method:
key_id:
verified_at:
expires_at:
supported_protocols:
declared_purpose:
```

Trust classes:

```text
UNKNOWN
DECLARED
CRYPTOGRAPHICALLY_VERIFIED
PARTNER
INTERNAL
```

Identity MUST NOT equal authorization.

Maintain this architecture:

```text
IDENTITY
Who is the actor?

DELEGATION
What did the principal authorize?

POLICY
Does the business allow this action?
```

Never collapse these into one boolean.

---

# 17. Request Integrity / Signatures

If implementing HTTP Message Signatures per the BRD:

Test:

- valid signature;
- invalid signature;
- unknown key;
- expired key;
- wrong key ID;
- missing signed component;
- changed body;
- wrong target;
- timestamp outside accepted window;
- nonce replay.

Do not implement custom cryptography.

Use maintained libraries where appropriate.

Document:

- algorithms;
- key lookup;
- timestamp tolerance;
- replay storage;
- failure semantics.

---

# 18. Delegated Authorization

Implement a `DelegationGrant` model.

Minimum fields:

```yaml
grant_id:
principal_reference:
agent_id:
provider_id:
capability_ids:
resource_boundary:
scopes:
value_limit:
currency:
geography:
valid_from:
expires_at:
confirmation_policy:
audience:
revoked:
```

Required denial cases:

- expired;
- revoked;
- wrong principal;
- wrong agent;
- wrong provider where constrained;
- wrong capability;
- wrong resource;
- wrong audience;
- value ceiling exceeded;
- geography constraint violated;
- insufficient scope.

Required warning case:

- materially broader scope than capability requires.

Do not create a proprietary OAuth replacement.

---

# 19. Participation Policy Engine

Create a deterministic policy engine.

Policy schema:

```yaml
policy_id:
subject:
  trust_class:
  provider_id:
  agent_id:

principal:
  type:

capability:
resource:
environment:

conditions:
  geography:
  time:
  value_limit:
  data_class:

required_confirmation:

decision:
  ALLOW
  DENY
  REQUIRE_HUMAN
  ALLOW_WITH_LIMITS

reason:
version:
effective_at:
expires_at:
owner:
```

State-changing capabilities MUST default deny.

Every decision MUST return:

```yaml
decision:
matched_policy:
policy_version:
reason:
missing_conditions:
required_next_action:
```

Implement policy linting.

Required lint checks:

- contradictory rules;
- unreachable rules;
- wildcard grants;
- missing default;
- expired rules;
- rule without owner;
- high-risk capability with no confirmation control;
- broad ALLOW masking explicit DENY;
- stale policy version.

---

# 20. Policy Determinism

Given identical:

- policy version;
- identity;
- delegation;
- capability;
- resource;
- environment;
- context;

the decision MUST be identical.

Add repeatability tests.

No LLM may be authoritative for access-control decisions.

---

# 21. Phase 2B Demonstration

Create one clearly state-changing synthetic capability.

Example:

```text
purchase
```

Evaluate it against:

```text
UNKNOWN
CRYPTOGRAPHICALLY_VERIFIED
PARTNER
INTERNAL
```

under one versioned policy.

Example only:

```text
UNKNOWN
→ DENY

VERIFIED
→ REQUIRE_HUMAN

PARTNER
→ ALLOW_WITH_LIMITS

INTERNAL
→ ALLOW
```

Do not hardcode outcomes.

The policy fixture must drive the result.

---

# 22. Phase 2B Adversarial Evaluation

Required categories:

## Ownership
- forged challenge;
- expired challenge;
- wrong host;
- replayed challenge.

## Identity
- unknown agent claiming trusted provider;
- invalid signature;
- expired key;
- replayed request;
- key mismatch.

## Delegation
- expired grant;
- revoked grant;
- wrong principal;
- wrong agent;
- wrong audience;
- excessive value;
- overbroad scope.

## Policy
- policy bypass;
- stale policy;
- broad ALLOW overriding DENY;
- missing default;
- wildcard privilege;
- unknown capability;
- expired policy.

## Cross-Protocol Identity
- same agent identity represented differently over MCP/A2A/OpenAPI;
- conflicting provider IDs;
- different capability identifiers mapping to same canonical capability.

---

# 23. Mutation Testing

Temporarily disable each critical control and prove tests fail.

Required mutations:

1. owner-verification requirement;
2. delegation expiry;
3. revocation;
4. principal binding;
5. audience binding;
6. policy default-deny;
7. explicit DENY handling;
8. signature replay protection;
9. over-value restriction.

Do not leave mutations in production code.

Document:

```text
control
mutation
expected failure
actual test caught?
```

A critical mutation surviving undetected is a Phase 2B release blocker.

---

# 24. Phase 2B Threat Model Update

Update:

```text
docs/security/V2_THREAT_MODEL.md
```

At minimum include:

- ownership verification takeover;
- agent impersonation;
- provider impersonation;
- stolen delegation;
- replayed delegation;
- signature replay;
- cross-user authorization reuse;
- overbroad scopes;
- confused deputy;
- policy bypass;
- stale policy;
- cross-protocol identity confusion.

Every threat MUST map:

```text
Threat
→ Preventive control
→ Detective control
→ Test
→ Eval
→ Residual risk
```

---

# 25. Governance Artifacts

Create/update:

```text
docs/governance/OWNERSHIP_VERIFICATION.md
docs/governance/ACTIVE_TESTING.md
docs/governance/POLICY_CHANGE_CONTROL.md
docs/governance/DATA_HANDLING.md
```

Rules:

- active testing requires verified ownership;
- environment classification is mandatory;
- production destructive simulation is off by default;
- every production policy has owner/version;
- policy changes are auditable;
- active-test artifacts have retention policy;
- Agent Native does not claim certification.

---

# 26. Phase 2B Exit Gate

Create:

```text
PHASE_2B_RELEASE_REVIEW.md
```

Status must be exactly one:

```text
PHASE_2B_READY
PHASE_2B_CONDITIONALLY_READY
PHASE_2B_NOT_READY
```

Required for READY:

- ownership verification implemented;
- both verification methods tested;
- identity model implemented;
- delegation model implemented;
- policy engine implemented;
- default-deny verified;
- deterministic decisions verified;
- all mandatory adversarial tests pass;
- all required mutation tests catch disabled controls;
- no critical/high unresolved security defect;
- v1 invariants remain intact;
- v2 CI passes.

---

# 27. Stop Before Phase 2C

For this work cycle:

```text
COMPLETE
Phase 2A closure
+
root migration
+
Phase 2B
```

Do NOT begin:

- simulator;
- transaction execution;
- receipts;
- active business actions;
- Agent Native Edge;

unless Phase 2B is independently `READY`.

If Phase 2B is not ready:

STOP.

Explain exactly why.

---

# 28. Required Progress Artifacts

Maintain:

```text
STATUS.md
```

Use:

```text
COMPLETE
IN_PROGRESS
BLOCKED
NOT_STARTED
DEFERRED_BY_BRD
```

Maintain:

```text
docs/V2_DECISION_LOG.md
```

Record consequential implementation decisions.

Update:

```text
docs/REQUIREMENTS_TRACEABILITY.md
```

for every completed requirement.

---

# 29. Final Verification Commands

At the end, run all applicable repository checks.

At minimum:

```text
format/lint
type checks
compile
unit tests
integration tests
protocol tests
security tests
adversarial evals
mutation-control tests
package build
clean installation
CLI smoke
v1 regression invariants
```

Do not claim readiness if mandatory tests are skipped.

---

# 30. Final Response Format

Report exactly these sections.

## 1. PHASE 2A CLOSURE

Include:

- YAML dependency fix;
- final Phase 2A test counts;
- skipped test count;
- eval count;
- final Phase 2A gate.

## 2. REPOSITORY MIGRATION

Include:

- branch used;
- v1 tag/release preserved;
- files moved;
- files merged;
- files removed;
- package namespace result;
- CLI result;
- duplicate `/v2` cleanup status.

## 3. V1 SECURITY REGRESSION STATUS

List each preserved invariant and PASS/FAIL.

## 4. PHASE 2B IMPLEMENTATION

List requirement IDs and components.

## 5. SECURITY RESULTS

List adversarial scenarios and findings.

## 6. MUTATION RESULTS

Show each disabled control and whether tests caught it.

## 7. TEST RESULTS

Counts by category.

## 8. EVAL RESULTS

Counts by category.

## 9. RESIDUAL RISKS

Be explicit.

## 10. RELEASE GATES

Show:

```text
PHASE_2A_READY | CONDITIONAL | NOT_READY
PHASE_2B_READY | CONDITIONAL | NOT_READY
```

## 11. NEXT ENGINEERING MILESTONE

Describe the exact Phase 2C entry criteria and recommended first implementation task.

---

# 31. Engineering Standard

This project is intended to demonstrate principal-level agent-systems engineering.

Optimize for:

- coherent repository/version strategy;
- clear system boundaries;
- secure protocol abstraction;
- deterministic policy;
- identity/authorization separation;
- failure isolation;
- evidence;
- adversarial thinking;
- testability;
- maintainability;
- explicit tradeoffs.

Do not optimize for:

- feature count;
- lines of code;
- superficial protocol support;
- green tests obtained by weakening expectations.

Before every consequential change ask:

1. What assumption are we making?
2. What could fail?
3. How could an attacker exploit it?
4. How would we detect that failure?
5. Is the control deterministic?
6. Is the result evidence-backed?
7. Is this v2 core, or a v3 sector concern?
8. Does this preserve v1's security guarantees?

---

# 32. Start Now

Proceed in this order:

1. inspect Git and release state;
2. close YAML dependency gap;
3. independently re-verify Phase 2A;
4. create migration plan and component matrix;
5. migrate v2 to root on the v2 development branch;
6. rerun all Phase 2A and v1 security regressions;
7. mark Phase 2A READY only if fully proven;
8. implement Phase 2B ownership;
9. implement identity;
10. implement delegation;
11. implement policy;
12. run adversarial tests;
13. run mutation tests;
14. produce Phase 2B release review;
15. stop before Phase 2C unless Phase 2B is READY.

Do not ask for permission between ordinary implementation steps.

Stop only if:

- Git state cannot be changed safely;
- a BRD requirement is materially ambiguous;
- a required protocol/specification cannot be accessed;
- a release gate fails and requires a product decision;
- or proceeding would violate a documented security boundary.

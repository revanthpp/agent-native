# Agent Native v2 — Build Continuation Directive

## Purpose

Use this file with the builder model to continue Agent Native v2 from:

- `PHASE_2A_READY`
- `PHASE_2B_CONDITIONALLY_READY`

Authoritative inputs:
- `Agent_Native_v2_Product_BRD.md`
- current `develop/v2` repository
- current Phase 2A/2B release-review artifacts
- existing v1 release evidence and tests

The BRD remains the product source of truth.

## Role

Act as Principal Engineer, Security Architect, Identity/Authorization Architect, Policy Architect, Protocol Engineer, Evaluation Lead, and Release Engineer.

Your job is to complete Phase 2B to a defensible release gate. Do not start Phase 2C unless Phase 2B is independently ready.

Optimize for:
- one canonical codebase;
- explicit trust boundaries;
- deterministic authorization;
- evidence-backed decisions;
- standards alignment;
- adversarial resilience;
- maintainability;
- explicit release gates.

Do not optimize for feature count or superficial green tests.

---

# 1. Non-Negotiable Product Principles

1. Agent access is a policy choice, not a maturity virtue.
2. Identity is not authorization.
3. Authorization is not policy.
4. Protocol conformance is not business safety.
5. State-changing actions fail closed.
6. Active testing requires verified ownership.
7. Unknown capabilities/trust remain explicit.
8. Target-controlled metadata cannot downgrade structural risk.
9. No raw secrets in reports, logs, traces, receipts, or eval artifacts.
10. No global readiness score.
11. No LLM may be authoritative for access-control decisions.
12. Every critical control needs adversarial tests and mutation tests.
13. Release readiness is determined by gates, not test count.

---

# 2. Canonical Repository Migration

The temporary `/v2` incubation structure MUST not remain the permanent product architecture.

Target state:

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

Requirements:
- preserve `v1.0.0` Git tag and history;
- work only on `develop/v2` or equivalent;
- canonical package namespace becomes `agentnative`;
- canonical CLI remains `agentnative`;
- production code must no longer depend on `agentnative_v2`;
- package build must contain one intended implementation;
- remove duplicate v2 tree only after root verification passes.

Create/update:
- `docs/migration/V2_ROOT_MIGRATION_PLAN.md`
- `docs/migration/V1_TO_V2_COMPONENT_MATRIX.md`

For each component classify:
`KEEP`, `REUSE`, `WRAP`, `MERGE`, `REPLACE`, `REMOVE_AFTER_MIGRATION`.

Migration rule:

```text
COPY/MERGE → TEST → VERIFY → REMOVE DUPLICATE
```

Never delete first.

---

# 3. Preserve v1 Security Invariants

After migration, independently prove:

1. raw artifact bodies never enter public reports;
2. credentials never leak;
3. `file://` network scans are rejected;
4. private-network SSRF remains blocked;
5. redirects are revalidated;
6. evidence provenance remains correct;
7. target metadata cannot downgrade mutation risk;
8. malformed advertised artifacts remain visible;
9. fatal scan failure returns nonzero exit;
10. target content remains data, never instructions.

Any regression blocks Phase 2B.

---

# 4. Complete Ownership Verification

Support:
- DNS TXT challenge;
- HTTPS `.well-known` challenge.

Minimum model:

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

Environment:
`SANDBOX`, `STAGING`, `PRODUCTION_READ_ONLY`, `PRODUCTION_ACTIVE`.

Requirements:
- exact-target binding;
- environment binding;
- expiration;
- replay resistance;
- subdomain separation;
- redirect-host validation;
- challenge material not logged raw;
- active testing denied without valid verification.

Adversarial cases:
- wrong token;
- expired token;
- replay;
- parent/sibling domain;
- redirect to other host;
- redirect to private host;
- stale DNS;
- copied challenge on another domain.

---

# 5. Complete Agent Identity

Model:

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
`UNKNOWN`, `DECLARED`, `CRYPTOGRAPHICALLY_VERIFIED`, `PARTNER`, `INTERNAL`.

Critical invariant:

> `CRYPTOGRAPHICALLY_VERIFIED` cannot be assigned unless cryptographic verification succeeded.

Identity must not grant permission by itself.

---

# 6. Implement HTTP Message Signature Verification

Use standards-aligned HTTP Message Signatures. Do not invent custom cryptography.

Verify:
- valid signature;
- invalid signature;
- unknown/wrong key;
- expired key;
- missing signed component;
- modified body;
- modified method;
- modified target URI;
- timestamp outside tolerance;
- unsupported algorithm;
- replayed request.

Document:
- algorithms;
- key lookup;
- covered components;
- timestamp tolerance;
- failure behavior.

For state-changing requests, failed signature verification MUST fail closed when verified identity is required.

---

# 7. Implement Replay Protection

At minimum:
- timestamp validation;
- nonce uniqueness;
- bounded replay window;
- provider/key/agent context binding;
- duplicate detection;
- expiration of replay entries.

Replay store may be in-memory for the reference implementation if:
- interface is replaceable;
- limitation is documented;
- semantics are deterministic.

---

# 8. Complete Delegated Authorization Verification

Do not confuse a `DelegationGrant` data object with verified delegation.

Minimum model:

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
verification_source:
verification_strength:
```

Must deny:
- expired;
- not-yet-valid;
- revoked;
- wrong principal;
- wrong agent;
- wrong provider where constrained;
- wrong capability;
- wrong resource;
- wrong audience;
- exceeded value;
- wrong geography;
- insufficient scope.

Warn on materially overbroad scope.

---

# 9. OAuth / Sender-Constrained Token Assessment

Do not build an identity provider or proprietary OAuth replacement.

Agent Native must assess relevant evidence for:
- authorization metadata;
- scopes;
- audience/resource indicators;
- redirect restrictions;
- token lifetime;
- PKCE where applicable;
- revocation where available;
- sender-constrained token support where available.

Result semantics must distinguish:
`DECLARED`, `OBSERVED`, `VERIFIED`, `NOT_OBSERVED`, `UNSUPPORTED`.

Where DPoP/sender-constrained proof is supported, test:
- valid proof;
- wrong key;
- replay;
- stale proof;
- wrong method;
- wrong URL;
- token/proof key mismatch;
- invalid nonce where applicable.

Absence MUST NOT automatically be labeled insecure.

---

# 10. Confused Deputy Defense

Mandatory deny scenarios:
- Agent B reuses Agent A's grant;
- same provider, wrong agent;
- same agent, wrong principal;
- capability A grant used for capability B;
- low-value grant reused for high-value action;
- resource X grant reused for Y;
- wrong audience.

A nearly valid grant still denies if any mandatory binding fails.

---

# 11. Participation Policy Engine Completion

Decisions:
`ALLOW`, `DENY`, `REQUIRE_HUMAN`, `ALLOW_WITH_LIMITS`.

State-changing capabilities default deny.

Every result returns:

```yaml
decision:
matched_policy:
policy_version:
reason:
missing_conditions:
required_next_action:
```

Requirements:
- deterministic;
- no LLM authority;
- explicit precedence;
- expired/future policy handling;
- explicit default;
- wildcard privilege detection;
- broad ALLOW vs explicit DENY handling.

---

# 12. Policy Change Audit

Every activated policy version is immutable.

Each update creates a new version.

Minimum audit record:

```yaml
policy_id:
old_version:
new_version:
changed_by:
changed_at:
change_summary:
change_hash:
```

Requirements:
- owner preserved;
- current version explicit;
- old versions auditable;
- receipts/evidence reference exact version used.

---

# 13. Policy Cache / Staleness

Scenario:

```text
policy v1 = ALLOW
policy v2 = DENY
```

The system MUST NOT silently continue authorizing under stale v1.

If caching exists:
- key includes policy version;
- invalidation on new version;
- TTL bounded;
- uncertain state fails closed for mutations.

If no cache exists, document that; do not add unnecessary complexity.

---

# 14. Policy Linting

Detect:
- contradictory rules;
- unreachable rules;
- wildcard privileges;
- missing default;
- expired/future rules;
- rule without owner;
- broad ALLOW masking explicit DENY;
- high-risk action without confirmation;
- duplicate ambiguity;
- inconsistent environment targeting.

---

# 15. Fail-Closed Authorization Pipeline

State-changing authorization must require:

```text
OWNER VERIFIED?
→ AGENT IDENTITY VALID?
→ REQUEST INTEGRITY VALID?
→ DELEGATION VALID?
→ CAPABILITY VALID?
→ POLICY DECISION?
→ CONFIRMATION if required
→ AUTHORIZED
```

If any required step is `FAILED`, `UNKNOWN`, `ERROR`, or `UNAVAILABLE`, default is `DENY`.

No silent allow.

---

# 16. Phase 2B Reference Scenario

Create one state-changing synthetic capability such as `purchase`.

Evaluate it for:
- UNKNOWN;
- CRYPTOGRAPHICALLY_VERIFIED;
- PARTNER;
- INTERNAL.

Demonstrate:
- real signature verification;
- replay protection;
- delegation binding;
- policy-dependent decisions;
- value limits;
- audience/principal binding;
- clear explanations.

Do not hardcode outcomes. The versioned policy fixture drives behavior.

---

# 17. Automated Mutation Harness

Build a repeatable harness that defeats controls one at a time and proves tests fail.

Required mutations:
1. bypass ownership verification;
2. bypass signature verification;
3. bypass replay protection;
4. allow expired grant;
5. ignore revocation;
6. ignore principal binding;
7. ignore audience binding;
8. ignore agent binding;
9. disable value ceiling;
10. default allow;
11. ignore explicit DENY;
12. ignore policy version;
13. disable secret redaction.

Output:

```yaml
mutation_id:
control:
mutation:
expected_test_failure:
actual_result:
caught:
```

A critical mutation that survives is a release blocker.

Restore source state after each mutation.

---

# 18. Adversarial Evals

Add fresh evals for:

### Ownership
forged/expired/replayed challenges, wrong host, sibling host, redirect to private host.

### Identity
unknown agent claiming partner, bad signature, expired key, changed body, replay.

### Delegation
expired, revoked, wrong principal/agent/provider/audience/resource/capability, over value/geography, insufficient or excessive scope.

### Policy
bypass, stale version, broad ALLOW vs DENY, missing default, wildcard privilege, unknown capability, expired policy.

### Cross-protocol
same identity represented differently over MCP/A2A/OpenAPI, provider mismatch, capability alias confusion.

---

# 19. Logging / Evidence Safety

Review all Phase 2B output paths.

Never expose:
- ownership challenge material;
- access/refresh/bearer tokens;
- private keys;
- raw sensitive signatures;
- unnecessary principal identifiers.

Inspect:
- CLI;
- JSON;
- Markdown;
- logs;
- exceptions;
- eval results;
- audit events;
- policy history.

Use hashes/references where possible.

---

# 20. Traceability and Threat Model

Update:

```text
docs/REQUIREMENTS_TRACEABILITY.md
docs/security/V2_THREAT_MODEL.md
```

Every requirement:

```text
BRD requirement
→ architecture
→ code
→ test
→ eval
→ evidence
→ release gate
```

Every threat:

```text
Threat
→ preventive control
→ detective control
→ test
→ eval
→ residual risk
```

Cover at minimum:
- ownership takeover;
- agent/provider impersonation;
- signature/token replay;
- stolen delegation;
- cross-agent/cross-user grant reuse;
- confused deputy;
- scope escalation;
- audience confusion;
- stale-policy authorization;
- policy bypass;
- cross-protocol identity confusion;
- secret leakage.

---

# 21. Governance

Update/create:

```text
docs/governance/OWNERSHIP_VERIFICATION.md
docs/governance/ACTIVE_TESTING.md
docs/governance/POLICY_CHANGE_CONTROL.md
docs/governance/DATA_HANDLING.md
```

Rules:
- active tests require ownership verification;
- environments labeled;
- destructive production simulation disabled by default;
- every policy owned/versioned;
- changes auditable;
- sensitive test artifacts have retention policy;
- Agent Native does not claim certification.

---

# 22. CI/CD

CI must run:
- formatting;
- lint;
- typing;
- unit;
- integration;
- protocol;
- security;
- adversarial evals;
- mutation harness;
- package build;
- clean install;
- CLI smoke;
- v1 invariant regressions.

Skipped critical tests fail the release gate.

---

# 23. Phase 2B Definition of Done

`PHASE_2B_READY` requires ALL:

- canonical root migration complete;
- compatibility bridge removed from production;
- ownership verification complete;
- cryptographic identity verification complete;
- replay protection complete;
- delegation verification complete;
- OAuth/sender-constrained-token assessment implemented to BRD scope;
- deterministic default-deny policy engine;
- policy version/change audit complete;
- stale-policy controls complete;
- mutation harness catches all critical mutations;
- adversarial evals pass;
- no critical/high unresolved defects;
- v1 security invariants remain intact;
- traceability complete;
- CI passes.

Create/update:

```text
PHASE_2B_RELEASE_REVIEW.md
```

Status exactly one:
`PHASE_2B_READY`, `PHASE_2B_CONDITIONALLY_READY`, `PHASE_2B_NOT_READY`.

---

# 24. Stop Before Phase 2C

Do NOT implement:
- active simulator transaction execution;
- receipts;
- production Agent Native Edge;
- sector packs.

Phase 2C begins only after independent verification of Phase 2B.

---

# 25. Final Build Report

Report:

1. Repository migration and bridge removal
2. Ownership verification
3. Identity/signature/replay
4. Delegation/OAuth/DPoP assessment
5. Policy/versioning/staleness
6. Mutation harness
7. Security findings
8. Test counts by category
9. Eval counts by category
10. v1 invariant status
11. residual risks
12. exact Phase 2B gate
13. exact Phase 2C entry criteria

Final engineering rule:

> Fix defect classes, not isolated symptoms.

Begin now.

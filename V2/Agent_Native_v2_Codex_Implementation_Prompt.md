# Agent Native v2 — Codex Implementation Prompt

## Role

You are the **Principal Engineer, Product Architect, Security Architect, Protocol Engineer, Evaluation Lead, and Release Engineer** responsible for implementing **Agent Native v2**.

You are working inside the existing `agent-native` repository.

The repository already contains the released v1 product. The v1 implementation is a working, security-hardened passive readiness scanner and MUST remain intact.

You have been provided:

- `Agent_Native_v2_Product_BRD.md`
- the existing Agent Native repository
- the v1 architecture, threat model, ADRs, evaluation assets, and release evidence already present in the repository

Your task is to:

> **Review the entire v2 BRD, map it against the current v1 implementation, create a clean v2 architecture inside a new `/v2` folder, and begin implementing v2 in the phased order defined by the BRD.**

The BRD is the authoritative product source of truth.

---

# 1. Non-Negotiable Source-of-Truth Rules

Before writing production code:

1. Read `Agent_Native_v2_Product_BRD.md` completely.
2. Read the existing v1 README, architecture, threat model, release review, relevant ADRs, and requirements traceability.
3. Inspect the v1 source implementation and existing tests/evals.
4. Create a gap analysis showing:
   - what v1 already satisfies;
   - what can be reused safely;
   - what must be redesigned;
   - what v2 adds;
   - what is explicitly deferred to v3.
5. Do not silently invent requirements.
6. Do not silently weaken requirements because implementation is difficult.
7. Do not silently upgrade or change protocol versions.
8. If the BRD and an external protocol specification conflict:
   - the external specification governs protocol correctness;
   - the BRD governs Agent Native product behavior, security posture, release gates, and scope.
9. If ambiguity remains, create an ADR before making a material design decision.

Do not begin by writing a large amount of code.

Begin by proving that you understand the product boundary.

---

# 2. Working Directory Constraint

All new v2 implementation work MUST live under:

```text
/v2
```

The existing v1 codebase is the released baseline.

Do not rewrite, move, or break v1 unless absolutely required for a shared security fix.

The v2 workspace should be self-contained enough to:

- install;
- test;
- run;
- develop independently;
- compare behavior against v1.

Suggested layout:

```text
v2/
  README.md
  pyproject.toml

  src/
    agentnative_v2/
      core/
      acquisition/
      protocols/
        openapi/
        mcp/
        a2a/
      capabilities/
      identity/
      delegation/
      ownership/
      policy/
      simulator/
      transactions/
      receipts/
      observability/
      gateway/
      evidence/
      reporting/
      security/
      config/

  tests/
    unit/
    integration/
    protocols/
    identity/
    ownership/
    delegation/
    policy/
    simulator/
    transactions/
    receipts/
    observability/
    security/
    adversarial/
    mutation/

  evals/
    protocols/
    identity/
    ownership/
    delegation/
    policy/
    simulator/
    transactions/
    security/
    baselines/
    manifests/
    results/

  docs/
    architecture/
    adr/
    security/
    evals/
    governance/
    protocols/
    remediation/

  examples/
    reference-business/
    reference-agents/
    scenarios/
```

You MAY adjust names if there is a strong architectural reason.

If you change the structure, document the reason in an ADR.

Do not create sector-specific folders under v2. Sector packs belong to v3.

---

# 3. High-Level Product Goal

Agent Native v1 answers:

> Can agents understand and potentially use this business?

Agent Native v2 must answer:

> Can this organization safely activate real agent access under explicit identity, authorization, policy, transaction, observability, and human-control boundaries?

The v2 execution model is:

```text
ASSESS
  ↓
VERIFY BUSINESS OWNERSHIP
  ↓
DISCOVER PROTOCOL SURFACES
  ↓
NORMALIZE CAPABILITIES
  ↓
IDENTIFY AGENT
  ↓
VERIFY DELEGATED AUTHORITY
  ↓
EVALUATE PARTICIPATION POLICY
  ↓
SIMULATE
  ↓
EXECUTE WITHIN CONTROLLED ENVIRONMENT
  ↓
VERIFY OUTCOME
  ↓
GENERATE RECEIPT
  ↓
TRACE + EVIDENCE
```

This is not a generic agent framework.

This is infrastructure for controlled business participation in the agent economy.

---

# 4. Mandatory Product Principles

Preserve these principles throughout implementation.

1. **Agent access is a policy decision, not a maturity virtue.**
2. **Identity is not authorization.**
3. **Protocol conformance is not business safety.**
4. **Active testing requires verified ownership.**
5. **State-changing actions fail closed.**
6. **Target-provided metadata cannot downgrade structural risk.**
7. **Evidence must be traceable.**
8. **Receipts are first-class artifacts.**
9. **No global readiness score.**
10. **No production destructive simulation by default.**
11. **Protocol adapters are modular.**
12. **Sector semantics do not belong in v2 core.**
13. **Deterministic logic is preferred for security and policy decisions.**
14. **LLMs must not be authoritative for access-control decisions.**
15. **Unknown protocol behavior must become an explicit limitation, not a PASS.**
16. **One failed adapter must not invalidate unrelated valid evidence.**
17. **Raw secrets must never enter public reports, traces, receipts, or eval artifacts.**
18. **Every critical control must have an adversarial test.**
19. **Every critical security control must have mutation testing.**
20. **Release readiness is determined by gates, not test count.**

---

# 5. Phase 0 — Mandatory Review Before Implementation

Create:

```text
v2/docs/V2_BRD_REVIEW.md
```

The review MUST include:

## 5.1 BRD Summary

Summarize the v2 product in your own technical language.

Explain:

- what changes from v1;
- why v2 exists;
- what v2 deliberately does not do;
- what is deferred to v3.

## 5.2 V1 Reuse Matrix

Create a table:

| V1 Component | Reuse | Wrap | Refactor | Replace | Reason |
|---|---:|---:|---:|---:|---|

Review at minimum:

- safe acquisition;
- network policy;
- evidence model;
- sanitization;
- reporting;
- OpenAPI parsing;
- existing check engine;
- threat model;
- secret detection;
- CI;
- fixtures;
- eval framework.

Do not duplicate hardened security code casually.

If code is reused, define how v2 imports or isolates it.

## 5.3 V2 Requirements Inventory

Enumerate every v2 requirement ID from the BRD.

Create:

```text
v2/docs/REQUIREMENTS_TRACEABILITY.md
```

Every requirement MUST map to:

```text
Requirement
→ Architecture component
→ Implementation module
→ Tests
→ Eval(s)
→ Release gate
→ Status
```

Statuses:

```text
NOT_STARTED
DESIGNED
IMPLEMENTED
VERIFIED
DEFERRED
BLOCKED
```

Only use `DEFERRED` when the BRD explicitly permits it.

---

# 6. Phase 1 — Architecture Before Feature Work

Create:

```text
v2/docs/architecture/V2_ARCHITECTURE.md
```

At minimum include diagrams for:

## 6.1 Component Architecture

```text
External Agent
      │
      ▼
Agent Native Edge
      │
      ├── Agent Identity
      ├── Delegation Verification
      ├── Capability Resolution
      ├── Participation Policy
      └── Observability
      │
      ▼
Protocol Adapters
      │
 ┌────┼────┐
 ▼    ▼    ▼
OAS  MCP  A2A
      │
      ▼
Capability Graph
      │
      ▼
Verified-Owner Simulator
      │
      ▼
Controlled Business Surface
      │
      ▼
Receipt + Evidence + Trace
```

## 6.2 Trust Boundaries

Explicitly identify:

- public target boundary;
- verified-owner boundary;
- external-agent boundary;
- principal/delegation boundary;
- protocol boundary;
- policy boundary;
- simulator boundary;
- downstream business-system boundary;
- receipt/evidence boundary;
- observability boundary.

## 6.3 Data Flow

Show where:

- credentials may exist;
- tokens may exist;
- secrets are prohibited from persistence;
- policy decisions occur;
- receipts are generated;
- traces are emitted.

## 6.4 Failure Domains

Show how the system behaves when:

- OpenAPI fails;
- MCP fails;
- A2A fails;
- identity verification fails;
- delegation verification fails;
- policy engine fails;
- downstream execution fails;
- receipt generation fails;
- tracing fails.

State-changing operations MUST fail closed when a required security decision cannot be completed.

---

# 7. Required ADRs Before or During Build

Create at minimum:

```text
v2/docs/adr/ADR-001-v2-isolated-workspace.md
v2/docs/adr/ADR-002-protocol-adapter-interface.md
v2/docs/adr/ADR-003-capability-graph.md
v2/docs/adr/ADR-004-owner-verification-boundary.md
v2/docs/adr/ADR-005-agent-identity-vs-authorization.md
v2/docs/adr/ADR-006-policy-default-deny.md
v2/docs/adr/ADR-007-simulator-environment-boundary.md
v2/docs/adr/ADR-008-receipt-integrity-model.md
v2/docs/adr/ADR-009-cross-protocol-trace-context.md
v2/docs/adr/ADR-010-protocol-version-pinning.md
```

Additional ADRs are expected when consequential design decisions arise.

---

# 8. Phase 2A — Protocol Foundation

This is the first implementation milestone.

Do NOT jump to the gateway or simulator before this is stable.

## 8.1 Protocol Adapter Interface

Implement a common adapter interface capable of:

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

Adapter output MUST include:

```yaml
protocol_family:
protocol_version:
adapter_version:
conformance_profile:
artifacts:
capabilities:
auth_requirements:
limitations:
evidence_refs:
```

Adapter failure MUST NOT crash unrelated adapters.

---

# 9. OpenAPI v2 Adapter Expansion

Implement support required by the BRD.

## 9.1 YAML

Add safe YAML parsing.

Security requirements:

- no arbitrary object construction;
- no executable tags;
- bounded input;
- bounded nesting where practical;
- malformed YAML fails safely;
- YAML parser behavior is explicitly tested.

## 9.2 `$ref`

Implement safe reference resolution.

Requirements:

- local references supported;
- same-origin remote references supported only through safe acquisition policy;
- private-network references blocked;
- `file://` blocked;
- recursive refs detected;
- max depth configured;
- max referenced documents configured;
- cycles produce explicit errors/limitations;
- source provenance survives ref resolution;
- one failed ref does not fabricate schema evidence.

## 9.3 Supported Version Detection

The adapter must explicitly report supported OpenAPI versions.

Do not silently accept unknown OpenAPI versions as compliant.

---

# 10. MCP Adapter

Pin the initial adapter to the protocol revision declared in the BRD.

Do not silently implement against "latest".

Create:

```text
v2/src/agentnative_v2/protocols/mcp/
```

The MCP adapter MUST support:

- endpoint/config discovery in controlled environments;
- server capability detection;
- tool inventory;
- resource inventory;
- prompt inventory;
- extension inventory;
- input schema extraction;
- output schema extraction;
- auth requirement extraction;
- tool risk classification;
- declared-vs-structural contradiction analysis;
- unsupported-feature limitations.

## MCP Safety Rules

Never assume:

```text
MCP compatible == trusted
```

Never allow tool descriptions to downgrade structural risk.

Never execute tools during passive conformance analysis.

Active tool invocation may occur only in the verified-owner simulator.

Create adversarial fixtures for:

- deceptive tool name;
- deceptive description;
- destructive behavior labeled read-only;
- malformed input schema;
- malformed output schema;
- unknown extension;
- excessive schema size;
- prompt-injection text inside descriptions.

---

# 11. A2A Adapter

Pin the adapter to the version declared in the BRD.

Create:

```text
v2/src/agentnative_v2/protocols/a2a/
```

Support:

- Agent Card parsing;
- required-field validation;
- advertised skill extraction;
- auth declaration extraction;
- capability normalization;
- task-state model representation;
- unsupported-feature limitations.

Do not assume that another A2A agent is trusted.

A2A compatibility and agent trust are separate findings.

---

# 12. Capability Graph

Implement the canonical capability representation.

Minimum fields:

```yaml
capability_id:
business_id:
name:
description:
protocol_sources:
action_class:
resource_types:
input_schema:
output_schema:
auth_requirements:
required_scopes:
side_effect:
reversibility:
confirmation:
idempotency:
value_boundary:
data_sensitivity:
human_escalation:
evidence_refs:
```

Required action classes:

```text
READ
RECOMMEND
PREVIEW
RESERVE
CREATE
UPDATE
DELETE
TRANSFER
PURCHASE
REFUND
UNKNOWN
```

## Capability Invariants

- the same semantic capability exposed through multiple protocols SHOULD normalize consistently;
- protocol-specific details MUST remain traceable;
- structural risk cannot be downgraded by descriptive metadata;
- every derived capability property MUST carry evidence;
- unsupported semantics MUST remain explicit.

---

# 13. Phase 2A Exit Gate

Do not proceed to identity/policy until this gate passes.

Create one controlled reference business that exposes equivalent capabilities using:

- OpenAPI;
- MCP;
- A2A.

Agent Native MUST normalize equivalent capabilities into semantically consistent capability objects while preserving protocol-specific provenance.

Required proof:

```text
Same business capability
      ↓
OpenAPI adapter ─┐
MCP adapter ─────┼─→ Canonical Capability
A2A adapter ─────┘
```

If outputs materially disagree, stop and resolve the abstraction before proceeding.

---

# 14. Phase 2B — Ownership, Identity, Delegation, Policy

Proceed only after Phase 2A exit gate passes.

---

# 15. Ownership Verification

Active testing MUST NOT occur against unverified targets.

Implement:

```text
DNS TXT challenge
HTTPS well-known challenge
```

At least both are required.

Ownership verification object SHOULD include:

```yaml
verification_id:
target:
method:
challenge:
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

v2 production-active destructive simulation MUST remain disabled by default.

Verification MUST bind to the exact target/environment.

Verification of one hostname MUST NOT automatically authorize another hostname.

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

Identity MUST NOT imply permission.

Required architecture:

```text
IDENTITY
Who is this agent?

AUTHORIZATION
What may this agent do?

POLICY
Should this specific request be allowed?
```

These MUST remain separate.

---

# 17. Request Integrity

Implement request-signature support where selected by the architecture.

If HTTP Message Signatures are implemented:

Test:

- valid signature;
- invalid signature;
- unknown key;
- expired key;
- missing covered component;
- timestamp outside allowed window;
- nonce replay;
- wrong target;
- payload modification.

Do not create custom cryptography.

Use well-maintained libraries where practical.

Document algorithm choices.

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

Required behavior:

- expired grant denied;
- revoked grant denied;
- wrong principal denied;
- wrong audience denied;
- wrong capability denied;
- value ceiling enforced;
- resource boundary enforced;
- overbroad scope detected.

OAuth evaluation must align with the BRD's referenced security baseline.

Do not implement an identity provider.

---

# 19. Participation Policy Engine

This is a core v2 component.

Create:

```text
v2/src/agentnative_v2/policy/
```

Minimum policy model:

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

## Policy Requirements

- default deny for state-changing capabilities;
- deterministic decisions;
- versioned policy;
- explicit explanation;
- matched-rule reference;
- missing-condition explanation;
- no adapter bypass;
- policy simulation without execution;
- stale/expired policy handling;
- contradiction detection;
- unreachable rule detection;
- wildcard privilege detection;
- missing-default detection.

Create a policy linter.

---

# 20. Phase 2B Exit Gate

Demonstrate one capability evaluated under at least four agent contexts:

```text
UNKNOWN
VERIFIED
PARTNER
INTERNAL
```

Expected outcomes MUST be policy-dependent.

Example:

```text
Search
  unknown   → ALLOW
  verified  → ALLOW
  partner   → ALLOW
  internal  → ALLOW

Purchase
  unknown   → DENY
  verified  → REQUIRE_HUMAN
  partner   → ALLOW_WITH_LIMITS
  internal  → ALLOW
```

This is only an example.

The policy file defines actual behavior.

The same request + same policy version MUST always produce the same decision.

---

# 21. Phase 2C — Verified-Owner Simulator

Do not build uncontrolled autonomous execution.

Create a simulator that operates against:

```text
SANDBOX
STAGING
```

by default.

Required scenario lifecycle:

```text
DISCOVER
→ AUTHENTICATE
→ AUTHORIZE
→ PREVIEW
→ POLICY_DECISION
→ CONFIRM
→ EXECUTE
→ VERIFY
→ RECEIPT
→ COMPENSATE if required
```

Every state transition must be explicit.

---

# 22. Simulator Safety Controls

Required controls:

- verified ownership;
- dedicated test principal;
- dedicated test agent;
- environment classification;
- hard timeout;
- hard request budget;
- hard value budget;
- side-effect ceiling;
- cancellation/compensation where applicable;
- no secret output;
- complete trace;
- receipt generation.

The simulator must refuse an execution above the environment's configured risk ceiling.

---

# 23. Failure Injection

Implement controlled failure scenarios:

- timeout before commit;
- timeout after commit;
- duplicate request;
- expired delegation;
- revoked delegation;
- stale quote;
- downstream 5xx;
- partial response;
- conflicting state;
- confirmation replay;
- wrong amount after approval;
- cancellation failure.

The purpose is to verify reliability behavior, not merely happy-path completion.

---

# 24. Transaction Safety Engine

Implement at minimum:

## Preview / Commit Separation

The system must distinguish preview from commit.

## Quote Identity

Where value can change, preserve:

```text
quote_id
value
currency
validity window
```

## TOCTOU

Test state changes between preview and commit.

## Idempotency

Test duplicate submission for mutation operations.

## Confirmation Binding

Confirmation must bind to the material action context.

A confirmation for:

```text
$100
```

must not authorize:

```text
$1,000
```

## Recovery

Model:

- retryable;
- terminal;
- compensatable;
- human escalation.

## Hidden Mutation

If a read/preview operation causes state change during controlled testing, classify this as a critical defect.

---

# 25. Receipt Engine

Every state-changing simulated action MUST produce a receipt.

Minimum schema:

```yaml
receipt_id:
timestamp:
business_id:
environment:
agent_id:
provider_id:
principal_reference:
capability_id:
policy_id:
policy_version:
decision:
delegation_reference:
confirmation_reference:
request_hash:
result:
side_effect:
resource_reference:
value:
currency:
correlation_id:
trace_id:
evidence_refs:
```

Receipt requirements:

- integrity verification;
- no raw secrets;
- minimize PII;
- link to trace;
- link to policy;
- link to delegation;
- tamper test.

---

# 26. Observability

Create structured events for:

```text
discovery
authentication
delegation
policy_decision
confirmation
execution
retry
failure
compensation
receipt
```

OpenTelemetry-compatible export is strongly preferred.

Cross-protocol workflows MUST preserve a root trace/correlation identifier.

Example:

```text
A2A request
    ↓
MCP tool
    ↓
HTTP API
    ↓
Receipt

All one trace.
```

Telemetry must not contain:

- access tokens;
- refresh tokens;
- passwords;
- payment credentials;
- secret headers;
- unnecessary personal data.

---

# 27. Phase 2C Exit Gate

Demonstrate controlled scenarios covering:

1. successful transaction;
2. duplicate retry;
3. stale quote;
4. expired authority;
5. policy denial;
6. human confirmation;
7. failed downstream execution;
8. compensating action;
9. forged receipt detection.

Do not proceed if any required high-risk control fails.

---

# 28. Phase 2D — Reference Agent Native Edge

The v2 gateway is a reference enforcement component.

It is NOT a replacement for enterprise API gateways.

Required sequence:

```text
REQUEST
  ↓
AGENT IDENTITY
  ↓
DELEGATION
  ↓
CAPABILITY
  ↓
POLICY
  ↓
EXECUTION DECISION
  ↓
CONTROLLED INVOCATION
  ↓
TRACE
  ↓
RECEIPT
```

Required controls:

- unknown-agent policy;
- replay protection;
- per-agent request limits;
- per-capability limits;
- circuit breaker;
- no arbitrary credential forwarding;
- fail closed for state-changing decisions;
- machine-readable denial reason;
- trace correlation.

---

# 29. Evaluation-First Development

Create:

```text
v2/docs/evals/V2_EVALUATION_STRATEGY.md
v2/docs/evals/V2_ACCEPTANCE_THRESHOLDS.md
v2/docs/evals/V2_KNOWN_LIMITATIONS.md
```

Every important product claim must have an eval.

---

# 30. Required Eval Domains

Implement evaluation coverage for:

1. OpenAPI YAML correctness;
2. `$ref` safety;
3. protocol adapter isolation;
4. MCP conformance;
5. A2A conformance;
6. capability normalization;
7. ownership verification;
8. agent identity;
9. delegated authorization;
10. policy determinism;
11. policy bypass resistance;
12. simulator state transitions;
13. transaction safety;
14. idempotency;
15. confirmation binding;
16. compensation;
17. receipt integrity;
18. cross-protocol tracing;
19. secret safety;
20. network safety;
21. anti-gaming;
22. failure isolation;
23. bounded resource usage;
24. mutation testing.

---

# 31. Adversarial Scenarios

At minimum add test/eval coverage for:

## Protocol

- malformed YAML;
- recursive ref;
- ref cycle;
- ref to localhost;
- ref to cloud metadata IP;
- MCP deceptive tool metadata;
- MCP malformed schema;
- unknown MCP extension;
- A2A malformed Agent Card;
- A2A capability mismatch;
- protocol version mismatch.

## Identity

- unknown agent claiming a known provider;
- valid provider with expired key;
- invalid signature;
- replayed signed request;
- signed request for unauthorized capability.

## Delegation

- expired grant;
- revoked grant;
- wrong principal;
- wrong audience;
- wrong resource;
- overbroad scope;
- value limit exceeded.

## Policy

- contradictory rules;
- broad ALLOW overshadowing DENY;
- stale policy;
- expired policy;
- missing default;
- wildcard privileges;
- unknown capability.

## Transaction

- duplicate commit;
- timeout before commit;
- timeout after commit;
- stale quote;
- confirmation replay;
- confirmation amount mismatch;
- partial success;
- rollback failure.

## Receipt

- modified receipt;
- wrong policy reference;
- wrong trace reference;
- changed request hash;
- duplicate receipt ID.

---

# 32. Mutation Testing

Temporarily disable critical controls and prove tests fail.

Required mutations:

- disable private-network ref protection;
- allow expired delegation;
- allow revoked delegation;
- bypass policy;
- change policy default to allow;
- disable confirmation binding;
- disable idempotency check;
- accept forged receipt;
- break trace correlation;
- disable secret redaction.

Document each mutation and whether the suite caught it.

A critical mutation that survives is a release blocker.

---

# 33. Security Threat Model

Create:

```text
v2/docs/security/V2_THREAT_MODEL.md
```

At minimum cover:

- agent impersonation;
- provider impersonation;
- stolen delegation;
- token replay;
- signature replay;
- authorization escalation;
- confused deputy;
- cross-user grant reuse;
- MCP tool poisoning;
- A2A capability spoofing;
- policy bypass;
- stale policy;
- TOCTOU;
- duplicate transaction;
- compensation failure;
- owner-verification takeover;
- receipt forgery;
- telemetry leakage;
- malicious partner agent;
- denial of service;
- denial of wallet;
- cross-protocol identity confusion;
- SSRF through protocol references.

Every threat must map to:

```text
threat
→ prevention
→ detection
→ test
→ eval
→ residual risk
```

---

# 34. Governance

Create or update within `/v2`:

```text
v2/docs/governance/ACTIVE_TESTING.md
v2/docs/governance/OWNERSHIP_VERIFICATION.md
v2/docs/governance/DATA_HANDLING.md
v2/docs/governance/POLICY_CHANGE_CONTROL.md
v2/docs/governance/RECEIPT_RETENTION.md
```

Required governance rules:

- active testing requires verified ownership;
- environment must be labeled;
- production destructive simulation is off by default;
- policies must be owned/versioned;
- sensitive capabilities may require mandatory human approval;
- policy changes are auditable;
- active-test artifacts have configurable retention;
- Agent Native does not claim certification.

---

# 35. CI/CD

Create v2 CI independently from v1.

Suggested workflow:

```text
.github/workflows/v2-ci.yml
```

The pipeline must:

- install v2 package;
- lint;
- type-check;
- unit test;
- integration test;
- protocol test;
- security test;
- adversarial eval;
- mutation-control checks where feasible;
- build package;
- verify clean install;
- verify critical CLI commands.

v1 CI must continue passing.

A v2 change must not silently regress v1.

---

# 36. CLI Direction

Target commands:

```bash
agentnative-v2 assess <target>
agentnative-v2 protocols <target>
agentnative-v2 capabilities <target>

agentnative-v2 owner verify <target>
agentnative-v2 owner status <target>

agentnative-v2 policy lint <policy>
agentnative-v2 policy evaluate <policy> <scenario>

agentnative-v2 simulate <target> --scenario <scenario>
agentnative-v2 simulate <target> --scenario <scenario> --dry-run

agentnative-v2 receipts verify <receipt>
```

The exact package/command naming may be adjusted, but v1 and v2 must not conflict.

Document the choice.

---

# 37. Do Not Build v3 in This Workstream

Do not implement:

- retail-specific checkout semantics;
- healthcare/FHIR sector logic;
- local-business onboarding flows;
- sector maturity models;
- UCP/ACP sector behavior;
- platform-specific Shopify/Toast/Square connectors;
- sector-specific policy packs.

v2 must create extension points for them, not implement them.

---

# 38. Delivery Strategy

Do NOT attempt a single giant v2 code dump.

Implement in this order:

```text
PHASE 0
BRD review + traceability

PHASE 1
Architecture + threat model + ADRs

PHASE 2A
Protocol foundation + capability graph

GATE 2A

PHASE 2B
Ownership + identity + delegation + policy

GATE 2B

PHASE 2C
Simulator + transaction safety + receipts + observability

GATE 2C

PHASE 2D
Reference Agent Native Edge

FINAL RELEASE GATE
```

If a gate fails:

STOP.

Fix the architecture or implementation before proceeding.

Do not paper over the failure.

---

# 39. Required Progress Artifacts

Maintain:

```text
v2/STATUS.md
```

Update after every phase.

Use:

```text
COMPLETE
IN_PROGRESS
BLOCKED
NOT_STARTED
DEFERRED_BY_BRD
```

Also maintain:

```text
v2/docs/V2_DECISION_LOG.md
```

Record material implementation decisions.

---

# 40. Initial Coding Objective

Your FIRST implementation objective is:

> Complete Phase 2A to release-quality standards.

That means:

1. v2 workspace exists;
2. requirements traceability exists;
3. architecture and threat-model baseline exists;
4. protocol adapter interface exists;
5. YAML OpenAPI works safely;
6. safe `$ref` resolution works;
7. MCP adapter parses/validates declared supported surfaces;
8. A2A adapter parses/validates declared supported surfaces;
9. canonical capability graph exists;
10. equivalent capabilities normalize consistently across three protocols;
11. security/adversarial evals for Phase 2A pass.

Only then proceed to Phase 2B.

---

# 41. Phase 2A Definition of Done

Phase 2A MUST NOT be called complete until:

- all mandatory 2A requirements have traceability;
- OpenAPI YAML tests pass;
- `$ref` recursion/cycle tests pass;
- private/local ref tests pass;
- MCP malicious-description tests pass;
- A2A malformed-card tests pass;
- adapter isolation tests pass;
- capability normalization tests pass;
- protocol provenance is intact;
- no raw secrets leak;
- v1 test suite still passes;
- v2 CI passes.

Create:

```text
v2/PHASE_2A_RELEASE_REVIEW.md
```

Final status must be exactly one of:

```text
PHASE_2A_READY
PHASE_2A_CONDITIONALLY_READY
PHASE_2A_NOT_READY
```

---

# 42. Final Response Format

At the end of your current coding session report:

## 1. BRD REVIEW
What you learned and any ambiguities.

## 2. V1 REUSE DECISIONS
What was reused, wrapped, refactored, or replaced.

## 3. ARCHITECTURE
Current v2 component architecture.

## 4. FILES CREATED / CHANGED
Exact paths.

## 5. REQUIREMENTS IMPLEMENTED
Requirement IDs.

## 6. TESTS ADDED
Counts and categories.

## 7. EVALS ADDED
Counts and categories.

## 8. SECURITY FINDINGS
Any unresolved issues.

## 9. PHASE GATE STATUS
Current gate result.

## 10. NEXT IMPLEMENTATION STEP
Exact next phase/backlog.

Do not claim more completion than has been demonstrated.

---

# 43. Final Engineering Standard

This project is intended to demonstrate principal-level applied agent-systems engineering.

Therefore optimize for:

- system boundaries;
- protocol abstraction;
- trust architecture;
- deterministic authorization;
- controlled autonomy;
- failure modes;
- observability;
- testability;
- evidence;
- versioning;
- maintainability;
- explicit tradeoffs.

Do not optimize for:

- feature count;
- flashy demos;
- lines of code;
- protocol logo collection;
- shallow "agent" wrappers.

Before every consequential decision ask:

> What assumption are we making?

> What could fail?

> How would an attacker exploit it?

> How would we know?

> Can we test it?

> Can we prove the result?

> Does this belong in v2 core, or is it actually a v3 sector concern?

---

# 44. Start Now

Begin now with:

1. complete BRD review;
2. v1 reuse/gap analysis;
3. v2 requirements traceability;
4. v2 architecture;
5. v2 threat-model baseline;
6. Phase 2A implementation;
7. Phase 2A tests and adversarial evals;
8. Phase 2A release review.

Do not ask for permission between normal implementation steps.

Stop only when:

- a requirement is materially ambiguous;
- a required external dependency/specification is inaccessible;
- a phase gate fails in a way requiring a product decision;
- or implementation would violate the BRD's security boundaries.

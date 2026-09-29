# Agent Native v3 — Phase 3 Build Requirements BRD
## Harden the Sector Pack Platform and Deliver the Retail Reference Journey

**Document status:** AUTHORITATIVE BUILD REQUIREMENTS  
**Version:** 1.0  
**Date:** 2026-09-28  
**Product:** Agent Native  
**Delivery scope:** Phase 3A hardening and Phase 3B Retail reference implementation  
**Audience:** Codex/build agents, product engineering, architecture, security, QA/evaluation, independent reviewers  

---

# 0. Execution Directive for Codex

This document is an implementation handoff. Codex MUST use it to inspect, update, test, and document the existing Phase 3 build.

Before changing code, Codex MUST read:

```text
Agent_Native_v3_Sector_Packs_BRD.md
BRD_GAP_REVIEW.md
PHASE_3A_BUILD.md
Agent_Native_v2_Product_BRD.md
AGENT_NATIVE_V2_PHASE_2C_TRANSACTION_IDENTITY_REMEDIATION.md
```

Codex MUST also inspect the actual repository, current tests, package configuration, CI configuration, architecture records, threat model, traceability artifacts, and independent audit folders. Document names or paths MAY differ; resolve the canonical equivalents rather than creating duplicates blindly.

The build MUST preserve the existing v2 control plane. Phase 3 MUST extend v2 through stable contracts and MUST NOT fork, bypass, replace, monkey-patch, or weaken v2 identity, delegation, policy, confirmation, transaction, receipt, evidence, observability, or evaluation behavior.

If this document conflicts with an existing requirement:

1. Preserve the stricter security or safety requirement.
2. Record the conflict in the build report.
3. Update the relevant BRD/ADR/traceability artifact.
4. Do not silently choose the easier implementation.

Codex MUST NOT self-certify a release gate reserved for independent audit.

---

# 1. Current Baseline

## 1.1 Product baseline

Agent Native v3 uses one horizontal Agent Native control plane with declarative sector packs.

```text
Agent Native Core
  ├── Identity and delegation
  ├── Policy and confirmation
  ├── Transaction safety
  ├── Capability graph
  ├── Simulation
  ├── Receipts and evidence
  ├── Observability
  └── Evaluation
         │
         ├── Retail Pack
         ├── Local Business / SMB Pack
         └── Healthcare Administration Pack
```

The product is a sector participation decision and validation system. It MUST be capable of recommending that a journey should not be activated when controls, evidence, economics, technical capacity, or operating readiness are insufficient.

## 1.2 Existing Phase 3A baseline

The existing build record states that Phase 3A contains:

- validated YAML manifests;
- core-version compatibility checks;
- sector namespace validation;
- capability compilation into the canonical `CapabilityGraph`;
- reversible registry enable/disable behavior;
- deterministic activation recommendations;
- multidimensional maturity assessment;
- pack evaluation categories;
- requirement-to-recommendation traceability;
- retail, healthcare administration, and local-business seed packs;
- pack list/show CLI commands.

The complete verification suite has not been evidenced as executed in a clean environment. Until it passes, the correct Phase 3A status is:

```text
IMPLEMENTED_UNVERIFIED
```

## 1.3 Inherited Phase 2C constraint

Phase 2C remains a blocking dependency for state-changing Phase 3 journeys until an independent re-audit proves:

- canonical logical transaction identity;
- idempotency binding to principal, agent, business, environment, capability, resource, and material payload;
- replay-safe confirmation within the same logical transaction;
- confirmation denial across different logical transactions;
- no blind re-execution after an unknown outcome;
- one logical side effect under retry and concurrency;
- accurate receipt and trace replay semantics.

Phase 3 design and non-mutating assessment work MAY continue. Phase 3 MUST NOT claim trustworthy transactional execution until the Phase 2C gate passes.

---

# 2. Product Goal

Deliver a production-style sector-pack platform that can:

1. load, validate, activate, version, upgrade, disable, and remove sector packs safely;
2. prove isolation between packs, tenants, environments, and sector semantics;
3. produce evidence-backed sector participation recommendations;
4. detect stale, conflicting, missing, or low-confidence evidence;
5. pin and monitor external protocol/profile versions;
6. simulate realistic state-changing journeys with failure injection and recovery;
7. inherit and verify the v2 control plane's safety guarantees;
8. produce an inspectable activation blueprint, test record, and residual-risk statement;
9. demonstrate measurable decision quality and implementation value;
10. provide a technically credible public artifact for principal-level agentic-systems roles.

---

# 3. Scope

## 3.1 In scope — Phase 3A hardening

- Formal pack application binary interface/API contract.
- Pack lifecycle, compatibility, provenance, integrity, and versioning.
- Core-gate inheritance and enforcement.
- Namespace, tenant, environment, and cross-pack isolation.
- Typed evidence, provenance, time, confidence, and unknown semantics.
- Activation recommendation correctness and explanation evidence.
- Protocol/profile version registry and drift detection.
- Pack supply-chain threat controls.
- Safe pack enable, disable, upgrade, downgrade, and removal behavior.
- Adversarial, property-based, fuzz, mutation, package, and clean-environment testing.
- CLI and machine-readable inspection surfaces.
- Architecture, threat-model, ADR, and traceability updates.

## 3.2 In scope — Phase 3B Retail

- Deep retail capability taxonomy.
- Retail journey state machine.
- Catalog, quote, checkout, order, cancellation, return/refund eligibility, and fulfillment simulation.
- UCP, ACP, OpenAPI, MCP, and A2A readiness/conformance profiles where support is explicitly implemented.
- Protocol-version pinning and compatibility reporting.
- Retail identity, delegation, confirmation, price, inventory, idempotency, recovery, and receipt controls.
- A generic reference commerce adapter and deterministic reference retail environment.
- Retail adversarial corpus, concurrency tests, and failure-injection tests.
- Retail activation blueprint and evidence bundle.

## 3.3 Seed-only scope

The Healthcare Administration and Local Business / SMB packs MAY remain design/seed packs during this delivery. They MUST continue to load and pass isolation/contract tests, but production connector or release-readiness claims are not required.

## 3.4 Out of scope

This delivery MUST NOT:

- become a payment processor, payment network, ecommerce platform, POS, EHR, or medical agent;
- hold raw card data unnecessarily;
- execute autonomous clinical decisions;
- claim legal, regulatory, clinical, payment-network, or universal protocol certification;
- create broad connector logo coverage without deep tests;
- introduce a second policy engine inside a sector pack;
- use an LLM as the sole decision authority for activation, maturity, policy, or release gates;
- start production hardening for all three sectors simultaneously;
- conceal known residual risks behind a composite readiness score.

---

# 4. Non-Negotiable Architecture Principles

## P3-ARCH-001 — One control plane — MUST

All packs MUST use the canonical v2 identity, delegation, policy, transaction, receipt, evidence, observability, and evaluation services.

## P3-ARCH-002 — Declarative extension — MUST

Pack behavior MUST be declared through documented contracts. Monkey-patching, undocumented import hooks, runtime mutation of core classes, hidden global state, and direct replacement of core services are prohibited.

## P3-ARCH-003 — Fail closed — MUST

A pack MUST fail closed when it is incompatible, unsigned where signatures are required, corrupted, stale beyond policy, partially loaded, missing a required dependency, or dependent on an unverified core guarantee.

## P3-ARCH-004 — Deterministic control decisions — MUST

Policy, compatibility, maturity gates, traceability gates, and release decisions MUST be deterministic and inspectable. An LLM MAY assist with explanation or classification only when bounded by deterministic schemas and evidence.

## P3-ARCH-005 — No activation is a valid outcome — MUST

The activation strategy engine MUST support:

```text
DIRECT
PLATFORM_MEDIATED
AGGREGATOR_MARKETPLACE
HUMAN_HANDOFF
DO_NOT_ACTIVATE
```

## P3-ARCH-006 — Evidence over assertion — MUST

No maturity, compatibility, conformance, safety, or readiness claim may pass solely because metadata declares it. Claims MUST link to executable evidence or an explicitly labeled human-reviewed record.

## P3-ARCH-007 — Environment separation — MUST

Design, test, sandbox, staging, and production MUST be first-class environments. Simulation credentials, endpoints, and policies MUST NOT reach production resources.

## P3-ARCH-008 — Depth before breadth — MUST

The Retail reference implementation MUST be completed and independently reviewed before production-hardening Healthcare Administration or Local Business / SMB.

---

# 5. Target Component Model

```text
Pack Source
  → Pack Integrity and Provenance Validator
  → Pack Loader and Compatibility Resolver
  → Pack Registry and Lifecycle Manager
  → Capability / Policy / Evaluation Compiler
  → Canonical v2 Control Plane
  → Activation and Maturity Engines
  → Simulator / Connector Boundary
  → Evidence, Receipts, Traces, and Reports
```

The following boundaries MUST remain explicit:

| Boundary | Responsibility |
|---|---|
| Pack | Sector semantics, capability taxonomy, sector risks, mappings, scenarios, report extensions |
| Core | Identity, authority, policy, confirmation, transaction safety, evidence, receipts, tracing |
| Protocol adapter | Interpret a versioned external standard/profile |
| Business connector | Interact with a particular platform/system |
| Simulator | Execute deterministic synthetic journeys and controlled failures |
| Recommendation engine | Select and explain participation patterns from typed evidence |
| Auditor | Independently validate claims and preserve immutable findings |

---

# 6. Canonical Pack Contract

## P3-PACK-001 — Manifest schema — MUST

Each pack MUST declare at least:

```yaml
pack_id:
pack_version:
pack_schema_version:
sector:
subsectors: []
lifecycle_state: draft | preview | active | deprecated | disabled
core_version_requirement:
required_core_guarantees: []
namespace:

provenance:
  source:
  publisher:
  created_at:
  build_id:
  content_hash:
  signature:
  signing_key_id:

dependencies:
  packs: []
  protocol_adapters: []
  connectors: []
  runtime_packages: []

capability_taxonomy:
risk_model:
maturity_model:
control_profiles:
protocol_profiles:
platform_profiles:
activation_strategies:
human_handoff_rules:
evaluation_scenarios:
evidence_requirements:
report_sections:
known_limitations:
external_reference_mappings:

effective_at:
deprecated_at:
sunset_at:
```

## P3-PACK-002 — Canonical identity — MUST

Pack identity MUST be deterministic over canonicalized content. Equivalent pack content MUST produce the same content hash. Non-semantic transport metadata MUST NOT alter pack identity.

## P3-PACK-003 — Namespace ownership — MUST

Capability, policy, evidence, evaluation, report, and external-mapping identifiers MUST be namespaced. Duplicate or ambiguous ownership MUST fail closed.

## P3-PACK-004 — Stable ABI — MUST

The implementation MUST document:

- allowed pack extension points;
- prohibited extension behavior;
- pack loader errors;
- compatibility resolution;
- serialization rules;
- lifecycle transitions;
- upgrade/downgrade semantics;
- storage migration behavior;
- deprecation and sunset behavior.

## P3-PACK-005 — Core guarantee inheritance — MUST

Transactional packs MUST declare their required core guarantees. Activation MUST be rejected when a required guarantee is not independently verified for the current core build.

Example:

```yaml
required_core_guarantees:
  - identity_binding_v1
  - delegation_scope_v1
  - transaction_identity_v1
  - replay_safe_confirmation_v1
  - idempotency_atomicity_v1
  - receipt_integrity_v1
```

## P3-PACK-006 — Safe lifecycle — MUST

Supported transitions MUST include:

```text
draft → preview → active → deprecated → disabled
```

Invalid transitions MUST be rejected. Emergency disablement MUST be supported independently of normal deprecation.

## P3-PACK-007 — Reversible disablement — MUST

Disabling or removing a pack MUST NOT:

- mutate canonical core behavior;
- leave active capability or policy registrations;
- corrupt stored results;
- delete historical evidence required for audit;
- make earlier receipts unverifiable.

Historical outputs MUST retain pack version and hash references.

## P3-PACK-008 — Upgrade impact report — MUST

Before activation of a new pack version, the system MUST report changes to:

- capabilities;
- controls;
- policies;
- protocols;
- evidence requirements;
- evaluation scenarios;
- recommendations;
- migrations;
- known limitations.

## P3-PACK-009 — Dependency transparency — MUST

All direct and transitive dependencies MUST be inspectable. Undeclared runtime dependencies MUST fail validation.

## P3-PACK-010 — Resource limits — MUST

Pack parsing and compilation MUST enforce configured limits for manifest size, nesting, reference count, scenario count, and processing time. Resource-exhaustion inputs MUST fail safely.

---

# 7. Evidence and Input Model

## P3-EVD-001 — Typed input observations — MUST

Activation and maturity inputs MUST use a typed structure:

```yaml
field_name:
  value:
  value_type:
  source_type: client_declared | observed | connector_evidence | test_result | expert_review
  source_ref:
  observed_at:
  valid_from:
  valid_until:
  confidence:
  environment:
  collector:
  evidence_hash:
```

## P3-EVD-002 — Unknown semantics — MUST

The system MUST distinguish:

```text
KNOWN_TRUE
KNOWN_FALSE
UNKNOWN
NOT_APPLICABLE
CONFLICTING
STALE
UNVERIFIED
```

Missing evidence MUST NOT be coerced to a favorable default.

## P3-EVD-003 — Time semantics — MUST

Evidence MUST define observation time, validity interval, timezone/UTC normalization, clock source where material, stale-after policy, and behavior under clock skew.

## P3-EVD-004 — Evidence minimization — MUST

Reports, logs, traces, fixtures, receipts, and recommendations MUST store only the sensitive content necessary to support the claim. Secrets, raw credentials, card data, and unnecessary personal or health data MUST be excluded or irreversibly redacted.

## P3-EVD-005 — Traceability — MUST

Every finding and recommendation MUST resolve:

```text
sector requirement
→ capability/control
→ evidence
→ evaluation
→ result
→ recommendation
```

Broken links, circular references, unknown IDs, or environment mismatches MUST fail validation.

## P3-EVD-006 — Evidence conflicts — MUST

Conflicting authoritative evidence MUST produce a visible conflict state. The engine MUST NOT silently select the most favorable source.

## P3-EVD-007 — Evidence integrity — MUST

Evidence records MUST support deterministic hashing and verification. Changes to material evidence MUST invalidate dependent results or trigger re-evaluation.

---

# 8. Activation Recommendation Engine

## P3-ACT-001 — Controlled inputs — MUST

The existing activation inputs MUST use controlled vocabularies, validation, provenance, and unknown handling. Free-text values MUST NOT directly drive deterministic release or activation decisions.

## P3-ACT-002 — Required outputs — MUST

Every recommendation MUST include:

```yaml
recommendation_id:
recommended_pattern:
viable_alternatives: []
rejected_patterns: []
rationale: []
evidence_refs: []
assumptions: []
unknowns: []
conflicts: []
prerequisites: []
security_implications: []
operating_model_implications: []
economic_implications: []
first_milestone:
residual_risks: []
pack_id:
pack_version:
pack_hash:
engine_version:
generated_at:
```

## P3-ACT-003 — Explainable rules — MUST

The engine MUST expose which rules and evidence materially caused the recommendation. It MUST NOT emit an unexplained composite score.

## P3-ACT-004 — Human override — MUST

Overrides MUST record:

- original recommendation;
- selected alternative;
- decision owner;
- rationale;
- timestamp;
- known risks accepted;
- required approval where configured.

An override MUST NOT bypass a hard security or safety prohibition unless a separate, explicitly authorized policy permits it.

## P3-ACT-005 — Economic viability — MUST

Where evidence is available, the engine MUST represent:

- expected agent-originated volume;
- protocol/platform fees;
- connector and inference cost;
- human-handoff and exception cost;
- margin or commission constraints;
- support burden;
- cost ceilings;
- abandonment thresholds.

Insufficient economics MAY produce `DO_NOT_ACTIVATE` or a limited pilot recommendation.

## P3-ACT-006 — Counterfactual behavior — MUST

Materially riskier inputs MUST NOT produce a less-controlled recommendation without explicit compensating evidence.

Required invariants include:

- increased data sensitivity cannot reduce required controls;
- reduced reversibility cannot increase autonomous authority;
- expired identity evidence cannot improve maturity;
- lower API maturity cannot reduce integration complexity;
- missing transaction-safety evidence cannot produce `L4 Transactable`;
- absent operating capacity cannot make an unsupported direct path preferable.

## P3-ACT-007 — Recommendation reproducibility — MUST

Identical canonical inputs, evidence, pack version, protocol versions, and engine version MUST produce semantically identical results.

---

# 9. Protocol and External Dependency Registry

## P3-PROTO-001 — Versioned profile — MUST

Every external protocol/profile mapping MUST record:

```yaml
profile_id:
protocol_name:
protocol_version:
profile_version:
as_of:
source_url:
source_hash:
retrieved_at:
supported_features: []
unsupported_features: []
required_extensions: []
compatibility_status:
last_drift_check:
drift_result:
```

## P3-PROTO-002 — No presence-based pass — MUST

The presence of an endpoint, manifest, agent card, product feed, FHIR metadata document, or protocol label MUST NOT produce a conformance, interoperability, or safety pass.

## P3-PROTO-003 — Drift detection — MUST

The system MUST detect and report:

- source hash changes;
- version changes;
- removed or renamed fields;
- changed required/optional semantics;
- breaking changes;
- newly required security behavior;
- unsupported newer versions.

## P3-PROTO-004 — Compatibility impact — MUST

Protocol drift MUST identify affected pack requirements, capabilities, connectors, scenarios, reports, and stored blueprints.

## P3-PROTO-005 — Initial drift fixture — MUST

Use the A2A v0.3-to-v1.0 transition as the first maintained drift fixture. Tests MUST verify detection of representative breaking changes rather than only comparing version strings.

## P3-PROTO-006 — Safe unsupported version behavior — MUST

An unsupported major version MUST fail closed for claimed conformance. The product MAY continue non-conformance assessment if the limitation is explicit.

---

# 10. Security Requirements

## P3-SEC-001 — Pack provenance and integrity — MUST

Active packs MUST have verifiable provenance and content integrity according to environment policy. Tampering MUST be detected before compilation or activation.

## P3-SEC-002 — Supply-chain control — MUST

The system MUST disclose and validate pack dependencies, connector dependencies, protocol-adapter dependencies, and runtime packages. Unpinned or disallowed dependencies MUST fail policy.

## P3-SEC-003 — Secret boundary — MUST

Pack files MUST NOT contain secrets. Connectors MUST obtain credentials through the canonical secret boundary. Secrets MUST be redacted from exceptions, reports, traces, receipts, and test artifacts.

## P3-SEC-004 — Tenant isolation — MUST

Pack configuration, evidence, recommendations, connector credentials, policy, results, and caches MUST be scoped to the correct tenant/business.

## P3-SEC-005 — Environment isolation — MUST

Every connector invocation MUST bind environment, endpoint allowlist, credential class, network policy, and permitted side-effect mode. Sandbox execution MUST reject production endpoints and credentials.

## P3-SEC-006 — Cross-pack isolation — MUST

Sector semantics, policies, capability IDs, evidence, and evaluation results MUST NOT resolve across unrelated packs unless an explicit shared-core contract permits it.

## P3-SEC-007 — Multi-actor identity — MUST

The architecture MUST support or explicitly model future actor chains:

```text
principal
→ consumer agent
→ intermediary/marketplace agent
→ merchant agent
→ payment/fulfillment service
```

At minimum, the Retail design MUST record actor identity, provider, tenant, delegated authority, capability, resource, environment, and correlation identifiers across hops.

## P3-SEC-008 — Authority attenuation — MUST

Delegated authority MUST NOT expand as it passes through an intermediary. Downstream scope MUST be equal to or narrower than upstream authority.

## P3-SEC-009 — Denial privacy — MUST

Denial and conflict responses MUST be machine-readable without exposing protected fraud logic, secrets, another tenant's data, prior transaction contents, or sensitive evidence.

## P3-SEC-010 — Threat delta — MUST

Each pack MUST publish a threat-model delta mapping:

```text
threat
→ preventive control
→ detective control
→ test
→ mutation
→ evidence
→ residual risk
```

---

# 11. Observability and Audit Requirements

## P3-OBS-001 — Required correlation — MUST

Where applicable, traces and evidence MUST correlate:

```text
tenant/business ID
environment
pack ID/version/hash
protocol/profile version
journey ID
logical transaction ID
principal ID/reference
agent ID/provider/reference
capability ID
policy version
recommendation ID
evidence references
connector invocation reference
receipt reference
```

## P3-OBS-002 — Replay semantics — MUST

A completed retry MUST show replay resolution and MUST NOT show a second business execution. The canonical business receipt MUST remain singular.

## P3-OBS-003 — Decision observability — MUST

Maturity and activation decisions MUST emit structured decision events containing evaluated rules, evidence references, unknowns, conflicts, result, and engine/pack versions.

## P3-OBS-004 — Redaction — MUST

Structured logs and traces MUST be tested for secret, personal-data, health-data, card-data, and cross-tenant leakage.

## P3-OBS-005 — Emergency actions — MUST

Pack disablement, capability kill switch, credential revocation, and policy emergency changes MUST emit auditable events.

---

# 12. Phase 3A Test Requirements

## 12.1 Clean environment and package tests

The builder MUST run and record:

```text
fresh editable install
dependency integrity check
full pytest suite
full unittest suite if maintained
wheel build
wheel install into a clean environment
package-content verification
CLI smoke tests from the installed wheel
```

No release conclusion may rely only on the source checkout.

## 12.2 Manifest contract tests

Required cases:

- minimum valid manifest;
- full valid manifest;
- malformed YAML;
- unknown required field;
- wrong field type;
- duplicate ID;
- namespace collision;
- incompatible core version;
- missing required core guarantee;
- missing dependency;
- circular dependency;
- stale pack;
- deprecated pack;
- invalid lifecycle transition;
- hash mismatch;
- signature mismatch;
- excessive nesting/size/reference count;
- partially loaded pack;
- unsupported schema version.

## 12.3 Lifecycle tests

Test:

```text
install → preview → activate → disable → reenable → deprecate → disable/remove
```

Verify after every transition:

- registry state;
- capability graph state;
- policy registrations;
- evaluation registrations;
- cached recommendations;
- historical evidence verification;
- receipt verification;
- no residual active behavior after disablement.

## 12.4 Property-based tests

Property-based tests MUST generate valid and invalid manifests, namespaces, compatibility ranges, dependency graphs, evidence records, and lifecycle sequences.

Required invariants:

- invalid input never mutates active registry state;
- disablement removes all active pack behavior;
- canonicalization is stable;
- equivalent manifests hash identically;
- namespace ownership remains unique;
- failed upgrades preserve the last valid active version;
- evidence from one tenant/pack cannot satisfy another tenant/pack's requirement.

## 12.5 Fuzz tests

Fuzz at least:

- manifest parser;
- version-range parser;
- identifier parser;
- external-reference parser;
- traceability graph input;
- protocol metadata parser;
- recommendation input deserializer.

Crashes, unbounded resource use, unsafe parser execution, partial activation, and sensitive error disclosure are failures.

## 12.6 Cross-pack and tenant isolation tests

Required:

```text
retail capability cannot resolve healthcare policy
healthcare evidence cannot appear in retail report
SMB disablement cannot mutate retail graph
tenant A evidence cannot satisfy tenant B gate
tenant A credentials cannot be selected for tenant B connector
same identifier suffix in two namespaces remains unambiguous
failed healthcare eval does not invalidate retail execution
```

## 12.7 Recommendation benchmark

Create a versioned, reviewable benchmark containing:

- clear direct-integration cases;
- clear platform-mediated cases;
- clear aggregator cases;
- clear human-handoff cases;
- clear `DO_NOT_ACTIVATE` cases;
- incomplete evidence;
- stale evidence;
- conflicting evidence;
- deceptive metadata;
- economically non-viable journeys;
- technically viable but operationally unsupported journeys.

Each case MUST contain expected outcome, critical controls, rationale, evidence, and reviewer identity/version.

Release thresholds:

- 100% pass on mandatory high-risk denial cases;
- 0 unsafe activation recommendations on the mandatory corpus;
- 100% evidence-reference integrity;
- 100% deterministic replay for identical canonical inputs;
- all noncritical disagreements adjudicated and documented;
- no unexplained recommendation change between engine versions.

## 12.8 Counterfactual and metamorphic tests

Change one material dimension at a time and verify expected directionality:

- API maturity;
- technical capacity;
- data sensitivity;
- regulatory sensitivity;
- reversibility;
- identity requirement;
- payment requirement;
- human capacity;
- evidence freshness;
- expected volume;
- action value;
- exception cost.

## 12.9 Mutation tests

Create production-sensitive mutations for at least:

```text
M-PACK-SKIP-COMPATIBILITY
M-PACK-SKIP-NAMESPACE
M-PACK-SKIP-SIGNATURE
M-PACK-SKIP-CORE-GATE
M-PACK-DISABLE-LEAK
M-EVIDENCE-ACCEPT-STALE
M-EVIDENCE-CROSS-TENANT
M-ACT-IGNORE-UNKNOWN
M-ACT-REMOVE-DO-NOT-ACTIVATE
M-PROTO-SKIP-VERSION
M-CONNECTOR-SKIP-ENVIRONMENT
```

All critical mutations MUST be killed by the ordinary maintained test suite. Toy-only mutations do not satisfy this requirement.

## 12.10 Protocol drift tests

Required:

- same version/same hash;
- same version/changed hash;
- newer compatible minor version;
- unsupported major version;
- removed required field;
- renamed operation;
- changed authentication requirement;
- changed error model;
- changed task/message representation;
- stale local profile;
- unavailable reference source.

## 12.11 Installed-wheel smoke tests

From the installed wheel, verify:

```text
agentnative packs list
agentnative packs show sector.retail
pack validation
compatibility failure
safe disablement
recommendation generation
traceability validation
protocol drift inspection
```

---

# 13. Phase 3A Exit Gate

Phase 3A is ready for independent review only when:

- pack ABI and lifecycle are documented and implemented;
- required core guarantees are declared and enforced;
- provenance/integrity validation passes;
- incompatible, malicious, stale, and partially loaded packs fail closed;
- cross-pack, cross-tenant, and cross-environment isolation passes;
- disablement leaves no active residue and preserves historical verification;
- evidence provenance, freshness, confidence, conflicts, and unknowns are enforced;
- recommendation benchmark and counterfactual tests pass;
- protocol drift detection passes the maintained A2A fixture;
- critical mutations are killed;
- clean install, wheel, CLI, and full regression suites pass;
- architecture, ADRs, threat model, and traceability are updated;
- an independent reviewer finds no open HIGH or CRITICAL issue.

Builder status MUST be exactly one of:

```text
READY_FOR_PHASE_3A_INDEPENDENT_REVIEW
PHASE_3A_NOT_READY
```

Only the independent reviewer may declare:

```text
PHASE_3A_READY
```

---

# 14. Phase 3B Retail Reference Implementation

## 14.1 Purpose

Retail is the first deep sector implementation because it stresses transaction identity, authority, price, inventory, confirmation, money semantics, concurrency, recovery, receipts, and protocol interoperability.

Phase 3B MUST deliver one end-to-end reference environment rather than shallow coverage of many platforms.

## 14.2 Required retail journey

The reference environment MUST support controlled simulation of:

```text
catalog discovery
→ product/variant selection
→ inventory observation
→ quote creation
→ shipping/tax/discount representation
→ confirmation where required
→ checkout submission
→ merchant order result
→ fulfillment-state retrieval
→ cancellation
→ return/refund eligibility assessment
```

Actual payment processing is out of scope. Payment authorization MAY be represented through a deterministic simulator or sandbox adapter.

## 14.3 Retail state model

The canonical retail state machine MUST define allowed transitions for at least:

```text
DISCOVERED
QUOTED
CONFIRMATION_REQUIRED
CONFIRMED
SUBMISSION_PENDING
ORDER_ACCEPTED
ORDER_REJECTED
UNKNOWN_OUTCOME
PARTIALLY_FULFILLED
FULFILLED
CANCEL_PENDING
CANCELLED
RETURN_ELIGIBLE
RETURN_INELIGIBLE
REFUND_PENDING
REFUNDED
RECONCILIATION_REQUIRED
MANUAL_ESCALATION
```

Invalid state transitions MUST fail closed and emit evidence.

## 14.4 Retail transaction inheritance

Every state-changing request MUST inherit the Phase 2C logical transaction model.

The transaction fingerprint MUST bind, where applicable:

```text
business/merchant
environment
principal
agent and provider
capability
resource/product/variant
material payload
amount and currency
quote identity
confirmation identity
shipping destination identity/reference
```

Non-material retry metadata MUST NOT create false conflicts.

## 14.5 Retail time and freshness

Retail observations MUST support:

- observed time;
- validity interval;
- stale-after policy;
- quote expiry;
- inventory freshness;
- timezone/UTC normalization;
- clock-skew handling;
- revalidation requirements at commit.

## 14.6 Retail identity and delegation

Retail policy MUST distinguish:

```text
unknown automation
recognized agent
verified commerce agent
partner agent
internal agent
```

Customer-specific pricing, loyalty, addresses, saved payment references, order history, and account data MUST require appropriate customer authority.

Intermediary identity MUST NOT substitute for principal authority.

## 14.7 Retail protocol profiles

The Retail pack MAY implement profiles for:

- Universal Commerce Protocol;
- OpenAI Agentic Commerce Protocol;
- OpenAPI commerce APIs;
- MCP commerce tools;
- A2A commerce agents;
- payment/trust profiles used only as supporting integrations.

Each claimed profile MUST identify exact supported versions and capabilities. Unsupported or partially supported behavior MUST be explicit.

## 14.8 Reference adapter and connector boundary

Build one generic reference commerce adapter with:

```text
discover_capabilities
map_to_capability_graph
test_connection
read_configuration
execute_sandbox_action
normalize_result
emit_trace
```

Every invocation MUST bind:

```yaml
environment:
endpoint_allowlist:
credential_class:
network_policy:
permitted_actions:
side_effect_mode:
```

## 14.9 Incident and dispute semantics

The Retail reference implementation MUST support evidence for:

- order reported successful but absent downstream;
- response lost after downstream success;
- unknown payment authorization outcome;
- duplicate order allegation;
- price or variant dispute;
- cancellation racing fulfillment;
- partial fulfillment;
- refund pending or failed;
- manual reconciliation.

Receipts MUST prove what Agent Native recorded without claiming facts it cannot establish.

---

# 15. Phase 3B Required Tests

## 15.1 Happy-path tests

- catalog discovery;
- unambiguous variant selection;
- fresh inventory;
- quote creation;
- valid confirmation;
- checkout accepted;
- order correlation;
- fulfillment retrieval;
- cancellation within policy;
- return eligibility assessment.

## 15.2 Identity and authority tests

- unknown agent purchase denied according to policy;
- verified agent with valid authority;
- verified agent with expired authority;
- valid agent but missing principal authority;
- changed principal using same idempotency key;
- changed agent/provider using same key;
- cross-merchant replay;
- cross-environment replay;
- intermediary identity laundering;
- delegated scope expansion attempt.

## 15.3 Price, quote, and product tests

- stale price;
- price increase before commit;
- price decrease before commit;
- changed currency;
- expired quote;
- changed quote under same key;
- wrong or ambiguous variant;
- coupon stacking;
- loyalty mismatch;
- shipping option invalidation;
- address change after confirmation.

## 15.4 Inventory and concurrency tests

- inventory loss between quote and commit;
- two buyers competing for last unit;
- repeated same transaction under concurrency;
- different transactions sharing confirmation;
- cancellation racing fulfillment;
- duplicate refund attempts;
- partial fulfillment update ordering;
- out-of-order status events.

For same logical transaction concurrency, run at minimum:

```text
8 workers × 25 rounds
```

Expected:

```text
one logical transaction
one confirmation binding
one downstream side effect
one canonical business receipt
coherent replay/wait results for all other callers
```

## 15.5 Failure-injection tests

Inject failure:

- before idempotency claim;
- after claim but before confirmation binding;
- after confirmation binding but before downstream call;
- after downstream success but before local persistence;
- after persistence but before response;
- during receipt generation;
- during trace emission;
- during cancellation;
- during connector timeout;
- during process restart.

The system MUST distinguish safe retry from unknown outcome and MUST never blindly duplicate a potentially completed side effect.

## 15.6 Connector boundary tests

- sandbox credential against production endpoint;
- production credential in simulation mode;
- unallowlisted endpoint;
- expired credential;
- connector outage;
- malformed response;
- success response without downstream order ID;
- duplicate downstream callback;
- secret in error payload;
- unsupported protocol version;
- declared capability with nonexistent executable operation.

## 15.7 Receipt and observability tests

Verify:

- order reference correlation;
- one receipt per logical action;
- replay trace without second execution span;
- pack/protocol/policy versions recorded;
- no secret or unnecessary personal data;
- unknown outcome represented honestly;
- compensation/reconciliation events correlated;
- receipt verification after pack upgrade or disablement.

## 15.8 Retail mutations

Add production-sensitive mutations for at least:

```text
M-RET-SKIP-INVENTORY-RECHECK
M-RET-SKIP-PRICE-RECONFIRM
M-RET-IGNORE-QUOTE-EXPIRY
M-RET-OMIT-VARIANT
M-RET-ALLOW-UNKNOWN-AGENT
M-RET-SKIP-DELEGATION
M-RET-DUPLICATE-CHECKOUT
M-RET-BLIND-UNKNOWN-RETRY
M-RET-SKIP-ENV-BINDING
M-RET-FALSE-SUCCESS-RECEIPT
```

---

# 16. Phase 3B Exit Gate

Phase 3B is ready for independent review only when:

- Phase 3A is independently ready;
- the required Phase 2C transactional guarantees are independently verified;
- the reference retail state machine is implemented;
- catalog-to-order-to-cancellation simulation works end to end;
- price, quote, inventory, identity, delegation, confirmation, and idempotency controls pass;
- lost-response and unknown-outcome scenarios do not create duplicate side effects;
- protocol mappings are versioned and evidence-backed;
- sandbox/production boundaries pass negative tests;
- receipts remain singular, correlated, verifiable, and accurately scoped;
- required adversarial, concurrency, failure-injection, mutation, clean-package, and installed-wheel tests pass;
- the retail activation blueprint includes assumptions, evidence, alternatives, implementation path, and residual risks;
- an independent reviewer reports no open HIGH or CRITICAL issue.

Builder status MUST be exactly one of:

```text
READY_FOR_PHASE_3B_INDEPENDENT_REVIEW
PHASE_3B_NOT_READY
```

Only the independent reviewer may declare:

```text
PHASE_3B_READY
```

---

# 17. Product-Value Validation

## P3-VALUE-001 — Decision-quality benchmark — MUST

Evaluate Agent Native against a human expert baseline using representative organization profiles. Compare:

- selected activation pattern;
- unsafe recommendations;
- missing controls;
- missing evidence;
- quality of assumptions;
- implementation sequencing;
- time to produce a defensible blueprint;
- reviewer confidence in the result.

## P3-VALUE-002 — Blind review — SHOULD

Where practical, sector/architecture reviewers SHOULD score generated blueprints without knowing whether they were produced manually or through Agent Native.

## P3-VALUE-003 — Value claims — MUST

The product MAY report measured decision time, evidence completeness, control recall, and implementation effort avoided. It MUST NOT claim financial ROI without observed client data.

## P3-VALUE-004 — Negative-value detection — MUST

The evaluation MUST include organizations for which direct activation, custom integration, or any state-changing agent journey is not justified.

---

# 18. Nonfunctional Requirements

## P3-NFR-001 — Determinism

Canonical inputs and versions MUST yield reproducible compatibility, maturity, traceability, and activation decisions.

## P3-NFR-002 — Performance

Establish and record baselines for pack validation, compilation, recommendation generation, report generation, simulation, and drift checks. Release SLOs MUST be set from measured baselines and intended operating scale rather than invented after implementation.

## P3-NFR-003 — Resilience

The system MUST tolerate connector timeouts, unavailable external references, partial evidence, process restarts, and duplicate/out-of-order events without unsafe state mutation.

## P3-NFR-004 — Portability

Core evaluation, simulation, and package verification MUST run in a clean documented environment without relying on an individual developer's machine state.

## P3-NFR-005 — Maintainability

Sector logic MUST remain in pack-owned modules. Core changes required by a pack MUST be justified as generally reusable contracts and protected by core regressions.

## P3-NFR-006 — Accessibility and human factors

Confirmation, denial, override, handoff, and kill-switch interfaces SHOULD be tested for comprehension, localization readiness, accessibility, timeout behavior, and approval fatigue.

## P3-NFR-007 — Test reproducibility

Concurrency, property, fuzz, mutation, and fault-injection runs MUST record seeds, versions, environment, configuration, and outcomes sufficient for reproduction.

---

# 19. Required Engineering Artifacts

The delivery MUST create or update:

1. Phase 3 architecture document.
2. Pack ABI and lifecycle specification.
3. ADR: sector packs versus sector forks.
4. ADR: pack provenance, integrity, and dependency policy.
5. ADR: evidence provenance, freshness, conflicts, and unknowns.
6. ADR: recommendation engine determinism and override semantics.
7. ADR: protocol versioning and drift management.
8. ADR: retail journey state and unknown-outcome recovery.
9. Phase 3 threat-model delta.
10. Requirement-to-code-to-test traceability matrix.
11. Phase 3A builder test report.
12. Phase 3B Retail builder test report.
13. Mutation report.
14. Clean-package and installed-wheel report.
15. Protocol compatibility matrix.
16. Recommendation benchmark and adjudication record.
17. Retail reference-environment guide.
18. Known limitations and residual-risk register.
19. Independent audit folder for each review iteration.
20. Public-safe architecture overview with no sensitive internal data.

---

# 20. Required Build Sequence

Codex MUST execute in this order unless a documented dependency requires a narrower change:

## Stage 0 — Baseline and inventory

- Inspect existing Phase 3 code and tests.
- Run the current suite before modification.
- Record existing failures separately from new regressions.
- Map existing implementation to this BRD.
- Mark each requirement `IMPLEMENTED`, `PARTIAL`, `MISSING`, or `BLOCKED`.

## Stage 1 — Protect the v2 boundary

- Verify the current Phase 2C status.
- Implement the `required_core_guarantees` contract.
- Block transactional activation when required gates are not verified.
- Add upstream regression coverage.

## Stage 2 — Harden the pack ABI

- Implement lifecycle, compatibility, provenance, integrity, namespaces, dependencies, and safe migrations.
- Add clean rollback on failed load/upgrade.
- Add CLI inspection.

## Stage 3 — Harden evidence and recommendations

- Implement typed observations, time, confidence, conflicts, and unknowns.
- Add `DO_NOT_ACTIVATE`.
- Add explanation/evidence output.
- Build the golden/counterfactual benchmark.

## Stage 4 — Add protocol drift management

- Implement version/source/hash registry.
- Add impact analysis.
- Add the A2A migration fixture.

## Stage 5 — Complete Phase 3A adversarial verification

- Property tests.
- Fuzz tests.
- Isolation tests.
- Mutation tests.
- Package/wheel/CLI tests.
- Builder report.
- Independent audit handoff.

## Stage 6 — Build the Retail reference environment

- Implement state model.
- Implement deterministic adapter/simulator.
- Bind inherited transaction controls.
- Implement failure and reconciliation states.

## Stage 7 — Complete Phase 3B verification

- Run scenario corpus.
- Run concurrency and fault injection.
- Run protocol/connector boundary tests.
- Run mutation and packaging regressions.
- Produce the Retail blueprint and evidence bundle.
- Prepare independent audit handoff.

---

# 21. Codex Change Discipline

Codex MUST:

- inspect before rewriting;
- preserve working v2 behavior;
- make the smallest coherent architectural change;
- use canonical domain models instead of duplicate pack-specific models;
- add tests with every material behavior change;
- update traceability and threat models in the same change set;
- record exact commands and results;
- preserve independent audit artifacts unchanged;
- expose residual risks honestly;
- stop and report `BLOCKED` if a required security dependency cannot be verified.

Codex MUST NOT:

- change tests merely to match incorrect behavior;
- weaken a requirement to make the suite pass;
- replace deterministic gates with prompt-only judgment;
- count mocked declarations as connector conformance;
- claim production readiness from happy-path tests;
- broaden scope into Phase 3C or 3D production work before Phase 3B closes;
- self-promote builder status to an independently controlled release status.

---

# 22. Builder Final Report Template

The final builder report MUST contain:

## 1. Executive status

Exactly one allowed builder status for each phase.

## 2. Baseline discovered

Repository version, environment, existing tests, and pre-existing failures.

## 3. Requirement coverage

Every requirement ID mapped to implementation, tests, evidence, and status.

## 4. Architecture changes

Components, boundaries, data models, lifecycle, and major tradeoffs.

## 5. v2 inheritance

How core guarantees are declared, verified, and enforced.

## 6. Security changes

Provenance, integrity, isolation, secret boundary, environment binding, and threat-model updates.

## 7. Evidence and recommendation changes

Typed observations, freshness, unknowns, conflicts, benchmark results, and override behavior.

## 8. Protocol drift

Registry design, drift fixture results, and impact analysis.

## 9. Retail reference journey

State model, connector/simulator behavior, and supported boundaries.

## 10. Adversarial results

Identity, authority, replay, concurrency, race, failure-injection, cross-pack, cross-tenant, and cross-environment results.

## 11. Mutation results

Mutation inventory, killed/survived status, restoration verification.

## 12. Package results

Clean install, dependency check, unit/regression counts, wheel, installed smoke, and CLI results.

## 13. Product-value results

Benchmark design, expert comparison, decision-quality findings, and limitations.

## 14. Documentation updated

ADRs, architecture, threat model, traceability, compatibility matrix, and operator guidance.

## 15. Residual risks

Explicit unresolved limitations and why they are acceptable or blocking.

## 16. Independent review handoff

Immutable evidence location and exact scenarios the reviewer must reproduce first.

---

# 23. Definition of Done

This delivery is complete only when Agent Native demonstrates all of the following:

```text
The core remains authoritative.
Packs are safe, versioned, inspectable extensions.
Bad packs fail closed.
Pack and tenant boundaries are proven, not assumed.
Evidence has provenance, freshness, confidence, and conflict semantics.
Recommendations can say “do not activate.”
Recommendation quality is benchmarked, not merely deterministic.
External protocol drift is detected and impact-mapped.
Retail is implemented as a stateful journey with failure and recovery.
Transactional behavior inherits independently verified v2 guarantees.
Retries, races, timeouts, and unknown outcomes do not duplicate side effects.
Receipts and traces tell the truth about what occurred.
Clean packages and installed artifacts pass.
Critical mutations are killed.
Independent reviewers—not builders—close release gates.
```

---

# 24. Final Product Positioning

Agent Native v3 MUST be demonstrable as:

> A sector-aware participation decision and validation control plane that helps organizations determine whether, where, and how external agents may safely interact with real business capabilities—and produces executable evidence when risk, economics, interoperability, or operating readiness make activation unjustified.

The portfolio signal is not the number of sector packs.

The portfolio signal is the rigor with which the system defines boundaries, anticipates failure, tests decisions, preserves evidence, and refuses unsafe autonomy.

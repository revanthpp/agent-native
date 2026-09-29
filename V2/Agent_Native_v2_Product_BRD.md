# Agent Native v2.0 Product BRD
## Assess → Activate: Protocol, Identity, Policy, Simulation, and Controlled Agent Access

**Document status:** AUTHORITATIVE PRODUCT SOURCE OF TRUTH
**Version:** 2.0 BRD
**Date:** 2026-09-27
**Product:** Agent Native
**Repository baseline:** `revanthpp/agent-native` v1.0.0
**Primary audience:** Product engineering, security, platform engineering, AI/agent architecture, QA/evaluation, open-source contributors, enterprise clients

---

# 0. How to Read This BRD

This document is normative for Agent Native v2.0.

The words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** express requirement strength.

Where this document references an external protocol or standard, the external source is authoritative only for that protocol's behavior. This BRD remains authoritative for what Agent Native builds, what it does not build, how protocol evidence is interpreted, security boundaries, release gates, evaluation criteria, and client-facing outputs.

If an external protocol changes after this BRD is published:

1. the existing adapter MUST remain pinned to its declared supported version;
2. a new protocol revision MUST be adopted explicitly;
3. an update MUST NOT silently change Agent Native result semantics;
4. regression tests MUST prove compatibility or document a breaking change.

---

# 1. Product Thesis

Agent Native v1 answered:

> **Can an AI agent understand and potentially do business with this organization?**

Agent Native v2 MUST answer the next question:

> **Can this organization safely activate real agent access, under explicit identity, authorization, policy, transaction, observability, and human-control boundaries?**

v2 moves Agent Native from a **passive readiness analyzer** to a **controlled agent-economy activation platform**.

```text
V1
Observe → Inspect → Explain

V2
Observe → Verify → Simulate → Govern → Activate → Prove
```

Agent Native MUST NOT assume that greater agent access is always better. A business may intentionally allow discovery but deny transactions, allow partner agents but block unknown agents, allow low-risk actions autonomously but require human confirmation for consequential actions, or participate only through an intermediary platform.

Core principle:

> **Agent Native optimizes for controlled participation in the agent economy, not maximum exposure to agents.**

---

# 2. v1 Baseline That v2 MUST Preserve

The current v1.0.0 repository establishes the following baseline:

- passive public-surface assessment;
- bounded HTTPS-oriented acquisition;
- private/loopback/reserved address protections;
- redirect validation;
- 20 deterministic checks (`AR-001` through `AR-020`);
- HTML and JSON OpenAPI inspection;
- evidence provenance;
- internal-artifact vs public-report separation;
- secret redaction and final output validation;
- conservative mutation classification;
- deterministic reference businesses;
- adversarial fixtures;
- threat model and ADRs;
- governance and responsible-use documents;
- independent release/security review artifacts.

v2 MUST preserve these trust boundaries.

Known v1 limitations that v2 is intended to address include:

- YAML OpenAPI;
- safe `$ref` handling;
- MCP conformance;
- A2A conformance;
- runtime delegated authorization verification;
- active idempotency/rollback testing;
- business ownership verification;
- verified-owner simulation;
- richer distributed tracing;
- hosted isolation design;
- property/fuzz testing;
- stronger supply-chain/SBOM controls.

---

# 3. Product Boundary

## 3.1 v2 IS

Agent Native v2 is a protocol-aware activation and verification platform that:

1. discovers machine-facing business capabilities;
2. validates protocol conformance;
3. normalizes capabilities across protocol families;
4. verifies target ownership before active testing;
5. models agent identity and trust;
6. models delegated principal authority;
7. evaluates business-owned agent participation policies;
8. safely simulates workflows in controlled environments;
9. tests transaction-safety properties;
10. generates machine-verifiable execution evidence;
11. produces traceable client activation guidance;
12. provides a reference policy-enforcement edge/gateway.

## 3.2 v2 IS NOT

v2 MUST NOT become:

- a consumer agent;
- an autonomous shopping assistant;
- a universal marketplace;
- a payment processor;
- a general API-gateway replacement;
- an identity provider;
- a certificate authority;
- a regulatory compliance certifier;
- a penetration-testing platform;
- an agent-ranking service;
- an LLM-based scoring engine;
- a sector-specific application;
- a hosted multi-tenant SaaS requirement for release.

Sector-specific business semantics belong to v3.

---

# 4. Primary Product Outcomes

A v2 business must be able to move through this lifecycle:

```text
1. ASSESS
   What machine-facing capabilities exist?

2. VERIFY
   Do I control the target environment?

3. NORMALIZE
   What can agents do across OpenAPI/MCP/A2A?

4. DEFINE PARTICIPATION
   Which agents may access which capabilities?

5. VERIFY AUTHORITY
   Who is the agent acting for and under what grant?

6. SIMULATE
   Can the workflow complete safely in a controlled environment?

7. ENFORCE
   Can runtime policy gate execution?

8. OBSERVE
   Can every material action be reconstructed?

9. PROVE
   Can Agent Native produce evidence explaining what happened?
```

---

# 5. Personas

## 5.1 Enterprise AI / Platform Architect

Needs protocol strategy, agent ingress patterns, capability exposure design, control-plane boundaries, and interoperability architecture.

## 5.2 Product / Digital Leader

Needs to decide which customer journeys agents may perform, which require human approval, and which channels should participate.

## 5.3 Security / IAM Leader

Needs to determine agent identity, principal authority, scopes, replay protection, policy enforcement, and revocation.

## 5.4 API / Integration Engineer

Needs protocol conformance, stable schemas, error semantics, retries, idempotency, and adapter behavior.

## 5.5 Governance / Risk Leader

Needs explicit autonomy boundaries, policy ownership, evidence, auditability, and residual-risk visibility.

## 5.6 Agent Ecosystem Partner

Needs discovery, authentication, authorization, capability contracts, confirmation semantics, receipts, and recovery behavior.

---

# 6. Canonical v2 Concepts

## 6.1 Business
The organization or service exposing capabilities.

## 6.2 Capability
A protocol-independent machine-usable business ability such as search, quote, reserve, purchase, schedule, cancel, refund, retrieve, or submit.

## 6.3 Protocol Surface
A machine-facing interface exposing capabilities. v2 MUST support OpenAPI, MCP, and A2A as first-class protocol families.

## 6.4 Agent
A software actor attempting to discover, negotiate, or execute a capability.

## 6.5 Agent Provider
The entity operating or distributing an agent.

## 6.6 Principal
The human, organization, or system authority on whose behalf an agent acts.

## 6.7 Agent Trust Class

v2 MUST support:

```text
UNKNOWN
DECLARED
CRYPTOGRAPHICALLY_VERIFIED
PARTNER
INTERNAL
```

Trust class describes identity/relationship strength only. It MUST NOT imply safety or authorization.

## 6.8 Delegation Grant

A grant MUST be able to express:

- principal reference;
- agent/provider reference;
- allowed capability;
- resource boundary;
- time boundary;
- optional value/amount boundary;
- optional geography/channel constraint;
- required confirmation;
- revocation state.

## 6.9 Agent Participation Policy
A business-owned rule that determines whether a given agent may perform a capability under a defined context.

## 6.10 Simulation
Controlled execution against a verified-owner sandbox, staging environment, or synthetic reference implementation.

## 6.11 Transaction
Any action with external state change or material consequence.

## 6.12 Receipt
A machine-readable record describing authorization, policy decision, attempted action, outcome, and evidence references.

---

# 7. High-Level Architecture

```text
                           AGENT ECOSYSTEM
                                  │
                     ┌────────────┴────────────┐
                     │                         │
                Passive Assessment       Verified Activation
                     │                         │
                     ▼                         ▼
              ┌─────────────┐           ┌──────────────┐
              │  Discovery  │           │ Agent Identity│
              └──────┬──────┘           └──────┬───────┘
                     │                         │
              ┌──────▼──────┐           ┌──────▼───────┐
              │ Protocol    │           │ Delegation   │
              │ Adapters    │           │ Verification │
              └──────┬──────┘           └──────┬───────┘
                     │                         │
                     └──────────┬──────────────┘
                                ▼
                       ┌─────────────────┐
                       │ Capability Graph │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │ Policy Decision │
                       │     Point       │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │ Simulator /     │
                       │ Reference Edge  │
                       └────────┬────────┘
                                ▼
               ┌────────────────────────────────┐
               │ Existing APIs / MCP / A2A /   │
               │ Controlled Business Systems    │
               └───────────────┬────────────────┘
                               ▼
                      Receipt + Telemetry
                               │
                               ▼
                         Evidence Store
```

---

# 8. Required Logical Components

v2 MUST contain separately testable components for:

1. Protocol Adapter Framework
2. OpenAPI Adapter
3. MCP Adapter
4. A2A Adapter
5. Capability Graph
6. Business Ownership Verification
7. Agent Identity Model
8. Delegation / Authorization Analyzer
9. Agent Participation Policy Engine
10. Verified-Owner Simulator
11. Transaction Safety Engine
12. Receipt Engine
13. Observability Model
14. Reference Agent Native Edge/Gateway
15. Evaluation Harness
16. Client Activation Report Generator

---

# 9. Protocol Adapter Framework Requirements

## V2-PROT-001 — Common adapter interface — MUST

Each protocol adapter MUST support these logical operations:

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

**Acceptance criteria**

- adapter behavior is versioned;
- adapter output maps to the canonical capability graph;
- unsupported features produce explicit limitations;
- one adapter failure does not crash others;
- target-controlled metadata never executes code.

## V2-PROT-002 — Protocol version pinning — MUST

Every result MUST identify protocol family, detected version, Agent Native adapter version, and conformance profile.

## V2-PROT-003 — Adapter isolation — MUST

A malformed MCP surface MUST NOT invalidate valid OpenAPI evidence, and vice versa.

## V2-PROT-004 — Adapter extension SDK — MUST

A contributor MUST be able to add a new protocol adapter without modifying the core check engine.

---

# 10. OpenAPI Expansion Requirements

## V2-OAS-001 — YAML OpenAPI — MUST

Agent Native MUST safely parse supported YAML OpenAPI documents without enabling arbitrary object construction or executable YAML tags.

## V2-OAS-002 — Version coverage — MUST

The adapter MUST declare supported OpenAPI releases. Initial target:

- 3.0.x;
- 3.1.x;
- 3.2.x where supported by the selected validator.

Unsupported semantics MUST produce explicit limitations.

## V2-OAS-003 — Safe `$ref` resolution — MUST

`$ref` handling MUST:

- support local references;
- support approved same-origin references under network policy;
- impose maximum depth;
- detect cycles;
- impose maximum reference count;
- pass every network reference through safe acquisition;
- block local-file dereferencing;
- block private-network dereferencing;
- preserve source provenance.

## V2-OAS-004 — Structural conformance — MUST

Results MUST use:

```text
VALID
VALID_WITH_WARNINGS
INVALID
UNSUPPORTED
```

## V2-OAS-005 — Operation normalization — MUST

Supported operations MUST normalize into the canonical capability model.

---

# 11. MCP Requirements

The initial MCP target MUST be pinned to **MCP specification revision 2026-07-28** unless superseded by an explicit ADR.

## V2-MCP-001 — Endpoint/server discovery — MUST
Agent Native MUST detect configured MCP surfaces in verified environments.

## V2-MCP-002 — Primitive inventory — MUST
The adapter MUST enumerate tools, resources, prompts, extensions, and advertised capabilities separately.

## V2-MCP-003 — Tool contract analysis — MUST
For each tool, determine where observable:

- input schema;
- output schema;
- side-effect potential;
- auth requirement;
- required confirmation;
- resource boundary;
- error semantics.

## V2-MCP-004 — Tool poisoning / contradiction detection — MUST

Natural-language descriptions MUST NOT lower structural risk. Contradictions among tool name, description, schema, declared behavior, and simulator behavior MUST be reported.

## V2-MCP-005 — Authorization profile — MUST
MCP authorization findings MUST be analyzed against the pinned MCP auth flow and Agent Native OAuth security requirements.

## V2-MCP-006 — Revision-specific behavior — MUST
The adapter MUST test behavior required by the pinned MCP revision and explicitly mark untested/unsupported features.

## V2-MCP-007 — Unknown extensions — MUST
Unknown extensions MUST NOT execute or silently alter policy.

---

# 12. A2A Requirements

The initial target MUST be pinned to **A2A 1.0.0** unless superseded by an explicit ADR.

## V2-A2A-001 — Agent Card validation — MUST
Validate required Agent Card fields and capability declarations.

## V2-A2A-002 — Skill normalization — MUST
Map A2A skills/capabilities into the common capability graph.

## V2-A2A-003 — Task lifecycle validation — MUST
The simulator MUST test supported task lifecycle states and terminal outcomes.

## V2-A2A-004 — Streaming — SHOULD
Where streaming is declared, controlled conformance testing SHOULD validate stream behavior.

## V2-A2A-005 — Authentication declaration — MUST
Identify A2A authentication requirements and compare them with business participation policy.

## V2-A2A-006 — Trust boundary — MUST
A2A compatibility MUST NOT imply agent trust.

---

# 13. Capability Graph Requirements

## V2-CAP-001 — Canonical capability object — MUST

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

## V2-CAP-002 — Action classes — MUST

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

## V2-CAP-003 — Monotonic risk — MUST
Target-supplied metadata MAY escalate risk or add detail but MUST NOT downgrade high-confidence structural risk.

## V2-CAP-004 — Evidence-backed derivation — MUST
Every derived field MUST retain source, derivation method, confidence, and evidence reference.

---

# 14. Business Ownership Verification

Active testing MUST be prohibited until ownership is verified.

## V2-OWN-001 — Active-test gate — MUST
Passive scans MAY remain anonymous. Active tests MUST require verified ownership/control.

## V2-OWN-002 — Verification methods — MUST
Implement at least:

1. DNS TXT challenge;
2. HTTPS well-known challenge.

## V2-OWN-003 — Environment classification — MUST

```text
SANDBOX
STAGING
PRODUCTION_READ_ONLY
PRODUCTION_ACTIVE
```

v2 MUST NOT enable destructive production-active simulation by default.

## V2-OWN-004 — Verification expiry — MUST
Verification MUST expire on a documented schedule.

## V2-OWN-005 — Target binding — MUST
Verification of one hostname/environment MUST NOT silently authorize another.

---

# 15. Agent Identity Requirements

## V2-ID-001 — Identity object — MUST

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

## V2-ID-002 — Identity != authorization — MUST
The product MUST keep identity and permission as separate decisions.

## V2-ID-003 — HTTP Message Signatures — SHOULD
The reference gateway SHOULD support RFC 9421-compatible signed requests for configured agents.

## V2-ID-004 — Replay defense — MUST
Signed-flow verification MUST include timestamp, nonce/replay control, key validity, algorithm policy, and covered-component validation.

## V2-ID-005 — Unknown agents — MUST
Unknown agents resolve to `UNKNOWN`; policy decides what happens next.

---

# 16. Delegated Authorization Requirements

## V2-AUTH-001 — OAuth security baseline — MUST
Where OAuth is used, evaluation MUST reflect current OAuth Security BCP principles such as exact redirect handling, PKCE where applicable, secure metadata use, and token protection.

## V2-AUTH-002 — Least privilege — MUST
Required capability permissions MUST be compared with granted scopes.

## V2-AUTH-003 — Excess privilege — MUST
Materially broader grants MUST produce a warning/failure according to policy.

## V2-AUTH-004 — Sender-constrained tokens — SHOULD
Detect and, where possible in controlled environments, validate DPoP or equivalent sender-constrained mechanisms.

## V2-AUTH-005 — Expiration — MUST
Expired authority fails closed.

## V2-AUTH-006 — Revocation — MUST
Revoked authority MUST not authorize new actions.

## V2-AUTH-007 — Principal binding — MUST
One principal's grant MUST NOT authorize another principal's action.

## V2-AUTH-008 — Resource/audience binding — MUST
Where semantics exist, grants/tokens MUST be evaluated against intended audience/resource.

---

# 17. Agent Participation Policy Engine

This is a central v2 differentiator.

## V2-POL-001 — Policy object — MUST

```yaml
policy_id:
subject:
  agent_trust_class:
  provider:
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
  ALLOW | DENY | REQUIRE_HUMAN | ALLOW_WITH_LIMITS
reason:
version:
effective_at:
expires_at:
```

## V2-POL-002 — Default deny for state-changing actions — MUST
If no rule authorizes a state-changing capability, the reference enforcement path MUST deny it.

## V2-POL-003 — Explicit read policy — MUST
Read access MAY use a different default, but it MUST be explicitly configured.

## V2-POL-004 — Determinism — MUST
Identical policy version + identity + authority + capability + context MUST return the same decision.

## V2-POL-005 — Explainable decisions — MUST
Every result MUST include decision, matched rule, reason, missing condition if denied, and required next action.

## V2-POL-006 — Policy linting — MUST
Detect unreachable rules, contradictions, wildcard privilege, missing default, expired rules, unowned rules, and high-risk actions without confirmation policy.

## V2-POL-007 — Adapter non-bypass — MUST
No protocol adapter may bypass policy.

## V2-POL-008 — Policy simulation — MUST
Policies MUST be evaluable without executing business actions.

---

# 18. Verified-Owner Simulator

## V2-SIM-001 — Sandbox/staging default — MUST
Active simulation defaults to `SANDBOX` or `STAGING`.

## V2-SIM-002 — Scenario lifecycle — MUST

```text
DISCOVER
→ AUTHENTICATE
→ AUTHORIZE
→ PREVIEW
→ POLICY_DECISION
→ CONFIRM if required
→ EXECUTE
→ VERIFY
→ RECEIPT
→ COMPENSATE if scenario requires
```

## V2-SIM-003 — Dry run — MUST
Every scenario MUST support dry-run behavior when the target or synthetic adapter permits it.

## V2-SIM-004 — Side-effect ceiling — MUST
The simulator MUST refuse to execute actions exceeding the environment's configured risk ceiling.

## V2-SIM-005 — Test identities — MUST
Use dedicated test identities, not production personal credentials.

## V2-SIM-006 — Value ceiling — MUST
Value-bearing actions MUST have hard configured maxima.

## V2-SIM-007 — State trace — MUST
Every run MUST record a complete state-transition trace.

## V2-SIM-008 — Compensation — MUST/SHOULD
Where reversibility is claimed and safe to test, compensation/cancellation SHOULD be actively verified. If it cannot be tested, limitation MUST be explicit.

## V2-SIM-009 — Failure injection — MUST
Support controlled injection of timeout-before-commit, timeout-after-commit, duplicate request, expired authority, stale quote, partial response, downstream 5xx, and conflicting state.

---

# 19. Transaction Safety Requirements

## V2-TXN-001 — Preview/commit separation — MUST
High-impact transactions MUST support or explicitly document absence of pre-commit preview.

## V2-TXN-002 — Quote identity — MUST
A quote/preview MUST carry an identifier and validity window where mutable price/value is relevant.

## V2-TXN-003 — TOCTOU testing — MUST
The simulator MUST test changed state between preview and commit.

## V2-TXN-004 — Idempotency — MUST
Mutation operations MUST expose or explicitly lack duplicate-suppression semantics. Controlled simulation MUST test duplicates where permitted.

## V2-TXN-005 — Confirmation binding — MUST
Required confirmation MUST be bound to action context so it cannot be reused for a materially different action.

## V2-TXN-006 — Recovery — MUST
Transactions MUST expose retry/terminal/cancel/compensate/escalate semantics where available.

## V2-TXN-007 — No hidden commit — MUST
A preview/read operation producing unapproved state mutation is a CRITICAL finding.

---

# 20. Receipt Engine

## V2-REC-001 — Receipt creation — MUST
Every simulated state-changing action MUST produce a receipt.

## V2-REC-002 — Receipt schema — MUST

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

## V2-REC-003 — Data minimization — MUST
Store references/hashes instead of raw secrets or unnecessary PII.

## V2-REC-004 — Integrity — MUST
Receipts MUST support tamper detection through a documented, tested integrity mechanism.

## V2-REC-005 — Correlation — MUST
Receipt trace/correlation identity MUST match observability records.

---

# 21. Observability Requirements

## V2-OBS-001 — Structured events — MUST
Emit events for discovery, authentication, delegation, policy decision, confirmation, execution, retry, failure, compensation, and receipt creation.

## V2-OBS-002 — OpenTelemetry — SHOULD
Reference implementation SHOULD export OpenTelemetry-compatible traces.

## V2-OBS-003 — Cross-protocol trace — MUST
A workflow crossing A2A → MCP → HTTP API MUST retain a common root trace/correlation reference.

## V2-OBS-004 — Redaction — MUST
Telemetry MUST NOT record access tokens, refresh tokens, raw credentials, payment credentials, secret headers, or unnecessary personal data.

## V2-OBS-005 — Decision observability — MUST
Policy decisions MUST be reconstructable without exposing sensitive policy inputs.

---

# 22. Agent Native Edge / Reference Gateway

The v2 gateway is a reference enforcement component, not a replacement for commercial API gateways.

## V2-GW-001 — Enforcement sequence — MUST

1. classify agent identity;
2. validate configured authentication;
3. evaluate delegation;
4. resolve capability;
5. evaluate participation policy;
6. enforce decision;
7. emit telemetry;
8. bind receipt context.

## V2-GW-002 — Unknown-agent behavior — MUST
Unknown agents MUST have explicit configured behavior.

## V2-GW-003 — Credential forwarding — MUST NOT by default
Agent-provided credentials MUST NOT be forwarded to arbitrary downstream services.

## V2-GW-004 — Abuse controls — MUST
Expose request budgets, per-agent limits, per-capability limits, replay checks, and circuit breakers.

## V2-GW-005 — Fail closed — MUST
If identity, delegation, or policy evaluation fails, state-changing actions MUST be denied.

## V2-GW-006 — Machine-readable denial — MUST
Return reason categories without exposing sensitive internal security details.

---

# 23. Client-Facing Outputs

## V2-REP-001 — Agent Participation Blueprint — MUST

Must include:

- discovered agent surfaces;
- protocol inventory;
- capability inventory;
- trust model;
- identity gaps;
- authorization gaps;
- participation-policy matrix;
- transaction-safety gaps;
- simulator results;
- observability gaps;
- recommended architecture;
- prioritized backlog.

## V2-REP-002 — Capability Exposure Matrix — MUST

Example:

| Capability | Unknown | Verified | Partner | Internal |
|---|---|---|---|---|
| Search | Allow | Allow | Allow | Allow |
| Quote | Deny | Allow | Allow | Allow |
| Purchase | Deny | Human confirmation | Allow with limit | Allow |
| Refund | Deny | Human confirmation | Limited | Allow |

The business owns the matrix.

## V2-REP-003 — Protocol Conformance Report — MUST
Keep protocol-specific findings evidence-backed and versioned.

## V2-REP-004 — Simulation Report — MUST
Show input, identity, authority, policy decision, trace, result, receipt, and recovery behavior.

---

# 24. CLI / DX Requirements

Target CLI:

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

agentnative report <run-id> --format json
agentnative report <run-id> --format markdown
```

The existing `scan` command SHOULD remain compatible through aliasing or documented migration.

---

# 25. Security Threat Model Additions

v2 MUST add threat coverage for:

1. agent impersonation;
2. provider impersonation;
3. stolen delegation;
4. replayed delegation;
5. token replay;
6. scope escalation;
7. confused deputy;
8. cross-user grant reuse;
9. agent/tool spoofing;
10. MCP tool poisoning;
11. A2A capability spoofing;
12. policy bypass;
13. policy shadowing;
14. stale policy cache;
15. TOCTOU between quote and commit;
16. duplicate transaction;
17. compensation failure;
18. malicious `$ref`/redirect resolution;
19. owner-verification takeover;
20. receipt forgery;
21. telemetry secret leakage;
22. compromised partner agent;
23. denial-of-wallet;
24. denial-of-service;
25. cross-protocol identity confusion.

Every threat MUST map:

```text
threat
→ preventive control
→ detective control
→ regression test
→ adversarial eval
→ residual risk
```

---

# 26. Governance Requirements

## V2-GOV-001 — Active-test authorization — MUST
Retain evidence that the target owner authorized active testing.

## V2-GOV-002 — Evidence environment label — MUST
Every report MUST identify evidence as one of:

```text
PUBLIC_PASSIVE
SANDBOX_ACTIVE
STAGING_ACTIVE
PRODUCTION_READ_ONLY
```

## V2-GOV-003 — No certification claims — MUST
Framework mappings MAY support assurance evidence but MUST NOT claim regulatory certification.

## V2-GOV-004 — Retention — MUST
Active simulation artifacts MUST follow configurable retention policy.

## V2-GOV-005 — Sensitive action registry — MUST
Businesses MUST be able to designate capabilities that always require human approval.

## V2-GOV-006 — Policy ownership — MUST
Every production policy MUST have an owner and version.

## V2-GOV-007 — Change audit — MUST
Capability/policy changes MUST produce audit records.

---

# 27. Evaluation Strategy

v2 release readiness MUST be based on demonstrated product claims, not test count.

Required evaluation layers:

1. parser correctness;
2. protocol conformance;
3. capability normalization;
4. identity correctness;
5. delegated authorization;
6. policy determinism;
7. policy bypass resistance;
8. simulator correctness;
9. transaction safety;
10. receipt integrity;
11. observability correlation;
12. secret/privacy safety;
13. network isolation;
14. anti-gaming;
15. failure isolation;
16. boundedness/performance;
17. developer experience;
18. mutation testing.

---

# 28. Mandatory Adversarial Scenarios

## Identity
- unknown agent claiming a trusted provider name;
- valid provider with expired key;
- wrong key ID;
- replayed signed request;
- valid identity with unauthorized capability.

## Delegation
- expired grant;
- revoked grant;
- wrong principal;
- wrong audience;
- wildcard scope;
- value-limit breach;
- geography restriction breach.

## Policy
- contradictory rules;
- deny overridden by broad allow;
- stale cached policy;
- missing default;
- unknown capability;
- incorrect trust-class promotion.

## Transactions
- duplicate commit;
- timeout before commit;
- timeout after commit;
- price/value changes after preview;
- confirmation replay;
- confirmation for action A used for action B;
- compensation failure;
- partial success.

## Protocol
- malformed YAML;
- recursive `$ref`;
- `$ref` to private IP;
- deceptive MCP tool description;
- malformed MCP schema;
- A2A Agent Card mismatch;
- A2A identity mismatch.

## Evidence
- modified receipt;
- evidence source mismatch;
- trace mismatch;
- secret reintroduced after sanitization.

---

# 29. Release Acceptance Thresholds

## Security blockers — ZERO tolerated

Release MUST be blocked by:

- unauthorized active execution;
- successful private-network fetch;
- local-file read through remote protocol;
- leaked credential/token;
- policy bypass for state-changing action;
- expired/revoked grant accepted;
- wrong-principal grant accepted;
- replay failure in a required signed flow;
- destructive action without required confirmation;
- duplicate transaction in required idempotency scenario;
- forged receipt accepted.

## Functional

- 100% mandatory protocol fixtures pass;
- 100% mandatory policy fixtures pass;
- 100% mandatory transaction-state fixtures pass;
- every supported version is reported;
- unsupported features become limitations, never silent PASS.

## Evidence

- 100% state-changing simulations generate receipts;
- 100% receipts correlate to trace data;
- 100% high-impact policy decisions are explainable;
- no public output contains raw secrets.

---

# 30. Engineering Baselines

For controlled local/reference environments:

- policy evaluation SHOULD be <50 ms p95 for standard policy sets;
- receipt generation SHOULD add <25 ms p95;
- simulations MUST have hard overall timeouts;
- retries MUST be bounded;
- active concurrency MUST be configurable;
- one adapter failure MUST NOT terminate other adapters.

These are engineering baselines, not client SLAs.

---

# 31. Build Phases

## Phase 2A — Protocol Foundation

Build:

- YAML OpenAPI;
- safe `$ref`;
- adapter SDK;
- MCP conformance;
- A2A conformance;
- canonical capability graph.

**Exit gate:** one reference business exposes equivalent capabilities through OpenAPI, MCP, and A2A, and Agent Native normalizes them consistently.

## Phase 2B — Identity + Participation Policy

Build:

- owner verification;
- agent identity;
- delegation model;
- OAuth assessment;
- policy engine;
- policy linting;
- capability exposure matrix.

**Exit gate:** the same capability is correctly allowed, denied, or human-gated for multiple trust classes under deterministic policy.

## Phase 2C — Active Simulator

Build:

- sandbox/staging simulator;
- transaction state machine;
- failure injection;
- idempotency;
- confirmation;
- compensation;
- receipts.

**Exit gate:** success, retry, duplicate, stale-state, and rollback scenarios can be reproduced without uncontrolled effects.

## Phase 2D — Reference Agent Native Edge

Build:

- policy enforcement point;
- agent recognition;
- replay controls;
- observability;
- OpenTelemetry export;
- client activation report.

**Exit gate:** a controlled agent request can be identified, authorized, policy-checked, executed against a sandbox capability, traced, and represented by a verifiable receipt.

---

# 32. v2 Definition of Done

v2 MUST NOT be called complete until:

- YAML OpenAPI and safe refs are implemented;
- MCP adapter passes its pinned conformance suite;
- A2A adapter passes its pinned conformance suite;
- capability graph is stable and documented;
- owner verification gates all active testing;
- policy engine is default-deny for state-changing actions;
- identity and authority are separate abstractions;
- verified-owner simulator exists;
- consequential transaction lifecycle is testable;
- receipts are integrity-verifiable;
- cross-protocol observability works;
- red-team coverage includes all required threat families;
- mutation tests prove critical controls are test-sensitive;
- v1 passive safety guarantees remain intact;
- a client-ready activation blueprint can be generated.

---

# 33. Explicitly Deferred to v3

v2 MUST NOT embed sector-specific semantics in core.

Deferred to v3:

- retail checkout/product semantics;
- healthcare administrative workflow semantics;
- local-business activation recommendations;
- sector maturity models;
- sector control packs;
- sector connector bundles;
- sector-specific eval scenarios;
- sector-specific external framework mapping.

v2 MUST expose clean extension points for these.

---

# 34. Key Product Decisions

1. Agent access is a policy choice, not a maturity virtue.
2. Identity does not equal authorization.
3. Protocol conformance does not equal business safety.
4. Active tests require verified ownership.
5. Destructive production execution is not a v2 default.
6. Target declarations cannot downgrade structural risk.
7. State-changing actions fail closed.
8. Receipts and evidence are first-class outputs.
9. No global readiness score.
10. Sector knowledge lives in v3 packs, not v2 core.

---

# 35. Recommended Repository Structure

```text
src/agentnative/
  core/
  acquisition/
  protocols/
    openapi/
    mcp/
    a2a/
  capabilities/
  identity/
  delegation/
  policy/
  ownership/
  simulator/
  transactions/
  receipts/
  observability/
  gateway/
  evidence/
  reporting/
  security/

packs/
  # reserved for v3

tests/
  unit/
  integration/
  protocol/
  identity/
  policy/
  simulator/
  transactions/
  security/
  adversarial/
  mutation/

evals/
  protocols/
  identity/
  policy/
  simulator/
  security/
  baselines/

docs/
  architecture/
  adr/
  security/
  evals/
  governance/
```

---

# 36. External Reference Baseline

These references inform protocol-specific requirements. They do not replace this BRD.

## Protocols

- Model Context Protocol, revision 2026-07-28
  https://blog.modelcontextprotocol.io/posts/2026-07-28/

- Agent2Agent Protocol, release 1.0.0
  https://a2a-protocol.org/v1.0.0/

- OpenAPI Specification
  https://spec.openapis.org/oas/

- JSON Schema 2020-12
  https://json-schema.org/draft/2020-12

## Authorization and Request Integrity

- RFC 9700 — OAuth 2.0 Security Best Current Practice
  https://www.rfc-editor.org/rfc/rfc9700.html

- RFC 9449 — OAuth 2.0 DPoP
  https://www.rfc-editor.org/rfc/rfc9449.html

- RFC 9421 — HTTP Message Signatures
  https://www.rfc-editor.org/rfc/rfc9421.html

## Observability

- OpenTelemetry Semantic Conventions
  https://opentelemetry.io/docs/specs/semconv/

---

# 37. Final Product Statement

Agent Native v2 is complete when it can credibly answer:

> **We know what this business exposes to agents, we know which agent is asking, we know what authority it has, we know what policy applies, we can safely simulate the intended workflow, we can observe the result, and we can prove what happened.**

That is the boundary between **agent-ready** and **agent-operable**.

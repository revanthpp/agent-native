# Agent Native v2 — Phase 2C Build Directive
## Verified-Owner Simulator, Transaction Safety, Receipts, and Observability

## Purpose

This file is the execution directive for **Phase 2C** of Agent Native v2.

Phase 2C begins only after:

```text
PHASE_2A_READY
PHASE_2B_READY
```

have both been independently verified.

Phase 2C turns Agent Native from a system that can:

- discover capabilities;
- verify ownership;
- identify agents;
- validate delegated authority;
- apply participation policy;

into a system that can:

> **safely simulate controlled agent actions, verify transaction behavior, produce evidence-backed receipts, and trace the full lifecycle of an agent-mediated interaction.**

This phase MUST remain aligned with:

- `Agent_Native_v2_Product_BRD.md`
- Phase 2A and Phase 2B architecture/ADRs
- current threat model
- requirements traceability
- existing v1 security invariants

The BRD remains the authoritative product source of truth.

---

# 1. Phase 2C Mission

The Phase 2C mission is:

> **Build a verified-owner, policy-controlled simulator for state-changing agent workflows that can safely exercise business capabilities in sandbox/staging environments, detect transaction-safety failures, and produce tamper-evident receipts and end-to-end traces.**

The desired lifecycle is:

```text
DISCOVER
  ↓
IDENTIFY AGENT
  ↓
VERIFY DELEGATION
  ↓
RESOLVE CAPABILITY
  ↓
POLICY DECISION
  ↓
PREVIEW / QUOTE
  ↓
HUMAN CONFIRMATION if required
  ↓
EXECUTE
  ↓
VERIFY OUTCOME
  ↓
COMPENSATE if required
  ↓
GENERATE RECEIPT
  ↓
EMIT TRACE / EVIDENCE
```

---

# 2. Phase 2C Is

Phase 2C MUST implement:

1. verified-owner simulator;
2. explicit scenario state machine;
3. environment/risk ceilings;
4. dry-run support;
5. controlled execution adapters;
6. transaction preview/commit separation;
7. quote identity and expiry;
8. TOCTOU detection;
9. idempotency testing;
10. confirmation binding;
11. retry behavior;
12. partial-failure handling;
13. rollback/cancellation/compensation testing;
14. failure injection;
15. receipt generation;
16. receipt integrity verification;
17. cross-protocol correlation and traces;
18. OpenTelemetry-compatible observability;
19. transaction-oriented adversarial evals;
20. mutation testing for critical Phase 2C controls.

---

# 3. Phase 2C Is Not

Do NOT build:

- production destructive execution by default;
- arbitrary production action execution;
- payments processing;
- a customer-facing agent;
- an ecommerce platform;
- a generic workflow orchestrator;
- a full API gateway;
- sector packs;
- healthcare/retail-specific semantics;
- autonomous business optimization;
- LLM-based authorization;
- opaque autonomous recovery.

Those belong to later phases or v3.

---

# 4. Entry Gate

Before writing Phase 2C production code, verify:

```text
PHASE_2A_READY
PHASE_2B_READY
```

and independently confirm:

- canonical root package exists;
- no production `agentnative_v2` bridge dependency remains;
- ownership verification is complete;
- cryptographic identity verification works;
- replay protection works;
- delegated authorization works;
- policy engine defaults deny;
- policy versioning/staleness controls work;
- v1 security invariants pass.

If any of these are false:

STOP.

Do not use Phase 2C to compensate for incomplete Phase 2B foundations.

---

# 5. Required Phase 2C Architecture

Create/update:

```text
docs/architecture/PHASE_2C_ARCHITECTURE.md
```

The architecture MUST include:

```text
Verified Business Environment
        │
        ▼
Ownership Gate
        │
        ▼
Simulation Scenario
        │
        ▼
Identity + Delegation
        │
        ▼
Capability Resolution
        │
        ▼
Policy Decision
        │
        ▼
Preview / Quote
        │
        ▼
Confirmation Gate
        │
        ▼
Execution Adapter
        │
        ▼
Outcome Verification
        │
        ├───────────────┐
        │               │
        ▼               ▼
     Success        Failure/Partial
        │               │
        ▼               ▼
     Receipt        Retry/Compensate
        │               │
        └───────┬───────┘
                ▼
             Trace
                │
                ▼
             Evidence
```

---

# 6. Required Phase 2C ADRs

Create at minimum:

```text
ADR-011-simulator-state-machine.md
ADR-012-environment-risk-ceilings.md
ADR-013-preview-commit-separation.md
ADR-014-idempotency-verification.md
ADR-015-confirmation-binding.md
ADR-016-compensation-model.md
ADR-017-receipt-integrity.md
ADR-018-cross-protocol-trace-context.md
ADR-019-failure-injection.md
ADR-020-dry-run-semantics.md
```

Create additional ADRs if major decisions arise.

---

# 7. Verified-Owner Simulator

Create a simulator module under:

```text
src/agentnative/simulator/
```

The simulator MUST NOT run active tests unless:

- ownership is valid;
- target environment is allowed;
- agent identity is valid;
- delegation is valid;
- policy permits the scenario.

---

# 8. Environment Classification

Supported environments:

```text
SANDBOX
STAGING
PRODUCTION_READ_ONLY
PRODUCTION_ACTIVE
```

Phase 2C execution rules:

## SANDBOX
Active controlled testing allowed.

## STAGING
Active controlled testing allowed with configured side-effect ceilings.

## PRODUCTION_READ_ONLY
Only read-only/verification scenarios allowed.

## PRODUCTION_ACTIVE
Destructive/state-changing simulation MUST remain disabled by default.

A production-active override, if architecturally retained for future use, MUST NOT be enabled in normal Phase 2C execution.

---

# 9. Risk Ceiling

Every environment MUST define an allowed risk ceiling.

Example:

```yaml
environment: STAGING

allowed_actions:
  - READ
  - PREVIEW
  - RESERVE
  - CREATE
  - UPDATE

blocked_actions:
  - TRANSFER
  - PURCHASE
  - REFUND
  - DELETE

max_value: 100
currency: USD
```

The simulator MUST refuse actions above the ceiling.

---

# 10. Simulation Scenario Model

Implement a scenario model.

Minimum schema:

```yaml
scenario_id:
name:
description:
business_id:
target_environment:
agent_identity:
principal:
delegation_reference:
capability_id:
input:
expected_risk:
expected_policy_outcome:
confirmation_behavior:
value_ceiling:
timeout_seconds:
retry_policy:
failure_injections:
expected_outcome:
compensation_required:
```

Every scenario MUST be versioned.

---

# 11. Scenario State Machine

Implement explicit states:

```text
CREATED
OWNER_VERIFIED
AGENT_VERIFIED
DELEGATION_VERIFIED
CAPABILITY_RESOLVED
POLICY_EVALUATED
PREVIEWED
AWAITING_CONFIRMATION
AUTHORIZED
EXECUTING
EXECUTED
VERIFYING
SUCCEEDED
FAILED
PARTIAL
COMPENSATING
COMPENSATED
RECEIPT_CREATED
TERMINAL
```

Transitions MUST be explicit.

Invalid transitions MUST be rejected.

Example:

```text
CREATED
→ EXECUTING
```

must be impossible.

---

# 12. Dry-Run Mode

Every scenario MUST support:

```text
--dry-run
```

where technically possible.

Dry-run MUST:

- resolve identity;
- resolve delegation;
- resolve capability;
- evaluate policy;
- calculate intended execution plan;
- identify required confirmation;
- identify expected side effects;
- identify limits;
- NOT perform the state-changing action.

Dry-run output MUST clearly distinguish:

```text
WOULD_ALLOW
WOULD_DENY
WOULD_REQUIRE_HUMAN
```

from actual execution.

---

# 13. Execution Adapter Boundary

Create an execution adapter interface.

Conceptually:

```text
prepare()
preview()
execute()
verify()
compensate()
```

Requirements:

- protocol-specific execution remains behind adapters;
- simulator core does not directly call arbitrary endpoints;
- execution adapters obey ownership and environment boundaries;
- credentials are scoped and protected;
- adapters cannot bypass policy.

---

# 14. Preview / Commit Separation

High-impact actions MUST distinguish:

```text
PREVIEW
```

from:

```text
COMMIT
```

If the target does not support preview:

- report limitation;
- do not fabricate preview semantics;
- determine whether policy allows execution without preview.

---

# 15. Quote Model

Where the action has economic/value semantics, implement:

```yaml
quote_id:
capability_id:
resource_reference:
value:
currency:
terms:
created_at:
expires_at:
version:
evidence_refs:
```

The quote MUST be bound to:

- resource;
- action;
- value;
- principal;
- business;
- environment.

---

# 16. TOCTOU Detection

Test:

```text
PREVIEW
→ state/value changes
→ COMMIT
```

Required behaviors:

- material change detected;
- stale quote rejected or reconfirmed according to policy;
- silent continuation prohibited when confirmation is required.

Examples:

- price changed;
- inventory changed;
- appointment slot vanished;
- resource version changed;
- terms changed.

---

# 17. Confirmation Binding

Human confirmation MUST bind to material action context.

Minimum confirmation object:

```yaml
confirmation_id:
principal_reference:
capability_id:
resource_reference:
value:
currency:
quote_id:
created_at:
expires_at:
confirmation_hash:
```

A confirmation for one action MUST NOT authorize another.

Test:

```text
approved $100
attempt $1,000
```

Expected:

```text
DENY / REQUIRE_NEW_CONFIRMATION
```

---

# 18. Confirmation Replay Protection

Confirmations MUST be:

- time-bound;
- context-bound;
- single-use where policy requires;
- invalid after material action changes.

Replay MUST be detected.

---

# 19. Idempotency

For state-changing actions, Agent Native MUST evaluate or verify duplicate-suppression behavior.

Model:

```yaml
idempotency_key:
capability_id:
principal:
request_hash:
created_at:
status:
result_reference:
```

Test:

```text
same request
same idempotency key
multiple submissions
```

Expected:

one logical transaction.

---

# 20. Duplicate Retry Scenario

Mandatory scenario:

```text
Agent sends commit
→ business succeeds
→ response lost
→ agent retries
```

Agent Native MUST determine whether this produces:

```text
one logical action
```

or:

```text
duplicate side effect
```

Duplicate side effect in a required idempotency scenario is a release blocker for that capability profile.

---

# 21. Retry Classification

The simulator MUST distinguish:

```text
RETRYABLE
TERMINAL
UNKNOWN
```

Failure classes.

Retries MUST be:

- bounded;
- policy-aware;
- idempotency-aware;
- observable.

No infinite retries.

---

# 22. Partial Failure

Support explicit partial outcomes.

Example:

```text
payment authorized
order creation failed
```

or:

```text
reservation created
confirmation delivery failed
```

The simulator MUST NOT collapse partial failure into either success or total failure.

Use:

```text
PARTIAL
```

and require recovery/compensation analysis.

---

# 23. Compensation / Cancellation

Where a capability claims reversibility:

- discover compensation capability;
- test in controlled environment where safe;
- verify state restoration or documented outcome;
- generate evidence.

Examples:

```text
create → cancel
reserve → release
order → cancel
update → restore
```

If compensation fails:

report explicitly.

---

# 24. Failure Injection Framework

Implement controlled failure injection.

Required injection points:

1. before preview;
2. after preview;
3. before policy decision;
4. before commit;
5. after commit but before response;
6. during response;
7. before verification;
8. during compensation.

Required failure types:

- timeout;
- connection reset;
- HTTP 5xx;
- partial payload;
- duplicate response;
- malformed response;
- stale resource;
- expired authorization;
- policy version change;
- downstream conflict.

---

# 25. Transaction Safety Engine

Create:

```text
src/agentnative/transactions/
```

Responsibilities:

- transaction lifecycle;
- preview/commit rules;
- quote validation;
- TOCTOU detection;
- idempotency;
- confirmation binding;
- retry classification;
- partial-failure handling;
- compensation state.

This engine MUST remain protocol-independent.

---

# 26. Hidden Mutation Detection

A declared read/preview operation that produces state change in controlled simulation is a critical defect.

Required test:

```text
operation declared READ
→ invoke in sandbox
→ state changes
```

Expected:

```text
CRITICAL FINDING
```

Target metadata MUST NOT suppress this result.

---

# 27. Receipt Engine

Create:

```text
src/agentnative/receipts/
```

Every successful or failed state-changing simulated action MUST produce a receipt.

Minimum receipt:

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
quote_reference:
request_hash:
result:
side_effect:
resource_reference:
value:
currency:
correlation_id:
trace_id:
evidence_refs:
integrity:
```

---

# 28. Receipt Integrity

Receipts MUST be tamper-evident.

Use a documented integrity mechanism.

Do not invent custom cryptographic primitives.

Acceptable reference approach:

- canonical serialized representation;
- cryptographic hash;
- optional signature using maintained cryptographic library.

Receipt verification MUST detect:

- changed decision;
- changed amount;
- changed resource;
- changed policy version;
- changed agent;
- changed trace ID;
- changed request hash.

---

# 29. Receipt Privacy

Receipts MUST NOT contain:

- raw access tokens;
- refresh tokens;
- private keys;
- payment credentials;
- unnecessary PII;
- full sensitive request bodies.

Use hashes/references.

---

# 30. Receipt Verification CLI

Target command:

```bash
agentnative receipts verify <receipt>
```

Return:

```text
VALID
INVALID
UNSUPPORTED
```

with evidence.

---

# 31. Observability

Create structured events for:

```text
simulation_started
ownership_verified
identity_verified
delegation_verified
capability_resolved
policy_decided
preview_created
confirmation_requested
confirmation_received
execution_started
execution_succeeded
execution_failed
retry_started
compensation_started
compensation_completed
receipt_created
simulation_completed
```

---

# 32. OpenTelemetry

The reference implementation SHOULD support OpenTelemetry-compatible traces.

Every event should include where appropriate:

```text
trace_id
span_id
correlation_id
scenario_id
capability_id
agent_id
business_id
environment
policy_version
```

Do not include secrets.

---

# 33. Cross-Protocol Trace

Mandatory demonstration:

```text
A2A request
→ MCP tool
→ HTTP/OpenAPI backend
→ receipt
```

All MUST retain one root trace/correlation identity.

---

# 34. Evidence Model

Every transaction finding MUST be traceable to:

```text
scenario
→ identity
→ delegation
→ policy
→ preview/quote
→ confirmation
→ execution
→ verification
→ receipt
→ trace
```

Evidence MUST be sanitized.

---

# 35. Phase 2C Security Threat Model

Update:

```text
docs/security/V2_THREAT_MODEL.md
```

Add:

- duplicate transaction;
- retry replay;
- confirmation replay;
- quote substitution;
- quote tampering;
- TOCTOU;
- stale price/resource state;
- hidden mutation;
- partial success ambiguity;
- failed compensation;
- forged receipt;
- receipt substitution;
- trace tampering;
- trace/receipt mismatch;
- simulator environment escape;
- credential reuse across environment;
- production target misclassification;
- denial-of-wallet;
- runaway retry loop.

Each threat:

```text
Threat
→ preventive control
→ detective control
→ test
→ eval
→ residual risk
```

---

# 36. Phase 2C Adversarial Scenarios

Mandatory:

1. duplicate commit;
2. timeout before commit;
3. timeout after commit;
4. response lost after successful commit;
5. stale quote;
6. changed amount after confirmation;
7. confirmation replay;
8. idempotency-key reuse for different payload;
9. expired delegation between preview and commit;
10. policy changes ALLOW → DENY between preview and commit;
11. resource changes between preview and commit;
12. compensation fails;
13. partial success;
14. hidden state mutation;
15. forged receipt;
16. modified receipt;
17. trace/receipt mismatch;
18. wrong environment;
19. risk ceiling exceeded;
20. infinite retry attempt.

---

# 37. Mutation Testing

Extend mutation harness.

Required Phase 2C mutations:

1. bypass ownership check before simulator;
2. bypass risk ceiling;
3. allow commit without policy;
4. allow commit without confirmation;
5. disable confirmation binding;
6. disable confirmation replay prevention;
7. disable quote expiry;
8. disable TOCTOU detection;
9. disable idempotency;
10. permit infinite retry;
11. convert PARTIAL to SUCCESS;
12. skip compensation failure reporting;
13. accept modified receipt;
14. break trace correlation;
15. leak raw secret into receipt.

Every critical mutation MUST be caught.

---

# 38. Simulator Test Corpus

Create reference scenarios:

## Happy Path
Valid owner, verified agent, valid delegation, allow policy, preview, confirmation, commit, verify, receipt.

## Denied
Policy denies before execution.

## Human Required
Policy requires confirmation.

## Duplicate Retry
Commit succeeds, response lost, retry occurs.

## Stale Quote
Quote expires before commit.

## Changed Value
Amount changes after approval.

## Expired Authority
Delegation expires before commit.

## Policy Changed
Policy changes from ALLOW to DENY mid-flow.

## Partial Failure
Downstream action partially completes.

## Compensation
Action succeeds then controlled rollback is invoked.

---

# 39. Phase 2C CLI

Target commands:

```bash
agentnative simulate <target> --scenario <scenario>
agentnative simulate <target> --scenario <scenario> --dry-run
agentnative simulate status <run-id>
agentnative receipts verify <receipt>
```

Output must clearly distinguish:

```text
DRY_RUN
EXECUTED
DENIED
FAILED
PARTIAL
COMPENSATED
```

---

# 40. Governance

Update/create:

```text
docs/governance/ACTIVE_TESTING.md
docs/governance/SIMULATION_ENVIRONMENTS.md
docs/governance/TRANSACTION_SAFETY.md
docs/governance/RECEIPT_RETENTION.md
```

Rules:

- active simulation requires ownership verification;
- production destructive execution off by default;
- test principals only;
- hard value ceilings;
- hard environment ceilings;
- retention configurable;
- receipts sanitized;
- compensation behavior documented;
- no claim that simulation proves universal production safety.

---

# 41. Phase 2C Evaluation Strategy

Create:

```text
docs/evals/PHASE_2C_EVALUATION_STRATEGY.md
docs/evals/PHASE_2C_ACCEPTANCE_THRESHOLDS.md
```

Evaluate:

1. state machine correctness;
2. invalid transition rejection;
3. dry-run safety;
4. risk ceiling enforcement;
5. preview/commit separation;
6. quote expiry;
7. TOCTOU detection;
8. idempotency;
9. confirmation binding;
10. replay;
11. retry behavior;
12. partial failure;
13. compensation;
14. receipt integrity;
15. trace correlation;
16. secret safety;
17. environment isolation;
18. failure injection;
19. mutation coverage.

---

# 42. Phase 2C Release Blockers

Zero tolerance for:

- active execution without verified ownership;
- state-changing execution after policy failure;
- execution above risk ceiling;
- destructive execution without required confirmation;
- confirmation reuse for different material action;
- duplicate side effect in required idempotency scenario;
- stale quote silently committed when reconfirmation required;
- hidden mutation from declared read operation;
- forged/modified receipt accepted;
- receipt contains raw secret;
- production environment executed when not allowed;
- infinite retry;
- policy changed to DENY but stale ALLOW still commits.

---

# 43. Phase 2C Exit Demonstration

Build one synthetic end-to-end scenario.

Example:

```text
Agent requests a controlled purchase-like action
```

Demonstrate:

```text
1. owner verified
2. agent verified
3. delegation verified
4. capability resolved
5. policy evaluated
6. quote generated
7. confirmation requested
8. confirmation bound to quote/value
9. commit executed in sandbox
10. result verified
11. duplicate retry safely handled
12. receipt generated
13. receipt validated
14. end-to-end trace available
```

Then rerun with:

```text
price/value changes before commit
```

Expected:

```text
REQUIRE_NEW_CONFIRMATION
or DENY
```

depending on policy.

---

# 44. Phase 2C Definition of Done

Phase 2C is READY only when:

- simulator exists;
- ownership gates active execution;
- state machine explicit;
- dry-run works;
- environment/risk ceiling enforced;
- execution adapters isolated;
- preview/commit separation works;
- quote identity/expiry works;
- TOCTOU detected;
- idempotency verified;
- confirmation bound to action;
- confirmation replay blocked;
- retries bounded/classified;
- partial outcomes represented;
- compensation modeled/tested;
- failure injection works;
- receipts generated;
- receipts tamper-detectable;
- cross-protocol trace works;
- OpenTelemetry-compatible export implemented or documented per BRD;
- Phase 2C mutation suite catches critical control defeat;
- no critical/high unresolved defect;
- v1/2A/2B regressions pass.

---

# 45. Release Review

Create:

```text
PHASE_2C_RELEASE_REVIEW.md
```

Status exactly one:

```text
PHASE_2C_READY
PHASE_2C_CONDITIONALLY_READY
PHASE_2C_NOT_READY
```

Do not start Phase 2D unless independently verified READY.

---

# 46. Required Final Build Report

Report:

## 1. Architecture
Simulator, transaction, receipt, observability components.

## 2. Scenario State Machine
States and transition guards.

## 3. Safety Controls
Environment/risk ceilings, ownership, confirmation, idempotency.

## 4. Transaction Engine
Preview, quote, commit, retry, compensation.

## 5. Receipt Engine
Schema and integrity mechanism.

## 6. Observability
Trace/correlation behavior.

## 7. Adversarial Tests
Cases and results.

## 8. Mutation Tests
Controls defeated and whether tests caught them.

## 9. Test Results
Counts by category.

## 10. Eval Results
Counts by category.

## 11. Regression Status
v1 + Phase 2A + Phase 2B.

## 12. Residual Risks
Explicit.

## 13. Gate
Exactly one:
`PHASE_2C_READY`, `PHASE_2C_CONDITIONALLY_READY`, `PHASE_2C_NOT_READY`.

## 14. Phase 2D Entry Criteria
Exact requirements for Agent Native Edge.

---

# 47. Final Engineering Standard

Phase 2C is the point where Agent Native crosses from:

```text
policy model
```

to:

```text
controlled autonomous action
```

Treat that boundary as high risk.

The core engineering question is:

> **Can we allow an agent to act, prove that it was authorized, prevent duplicate or stale execution, recover when something goes wrong, and reconstruct exactly what happened?**

Do not declare Phase 2C complete until the answer is demonstrably yes.

Begin only after Phase 2B is independently READY.

# Agent Native v3 — RC1 Hardening and Audit Readiness BRD
## Close the Phase 3A/3B Trust Boundaries Before Starting Another Sector

**Document status:** AUTHORITATIVE NEXT-BUILD REQUIREMENTS
**Version:** 1.0
**Date:** 2026-09-28
**Product:** Agent Native
**Target branch:** `feature/phase3-sector-packs`
**Reviewed baseline commit:** `5f8565d792e58b699bab203ea5ac8c24b9f9ed3d`
**Delivery target:** Phase 3 Release Candidate 1 audit readiness
**Audience:** Codex/build agents, independent auditors, maintainers, security reviewers, QA/evaluation

---

# 0. Codex Execution Directive

This document defines the next implementation slice after commit `5f8565d`.

The current build is substantial but honestly remains:

```text
Phase 3A: PHASE_3A_NOT_READY
Phase 3B: PHASE_3B_NOT_READY
```

The next build MUST close the known trust, durability, connector, and verification boundaries. It MUST NOT begin production hardening for Local Business / SMB or Healthcare Administration.

Before modifying code, Codex MUST inspect the current branch and read:

```text
V3/Agent_Native_v3_Phase_3_Build_Requirements_BRD.md
V3/PHASE_3_BUILD_REPORT.md
V3/REQUIREMENTS_TRACEABILITY.md
docs/architecture/PHASE_3_ARCHITECTURE.md
docs/security/PHASE_3_THREAT_MODEL.md
AGENT_NATIVE_V2_PHASE_2C_TRANSACTION_IDENTITY_REMEDIATION.md
```

Codex MUST also inspect:

```text
src/agentnative/packs/
src/agentnative/transactions/
src/agentnative/receipts/
src/agentnative/observability/
tests/packs/
tests/transactions/
evals/phase3/
audit_v2/
pyproject.toml
CI/workflow configuration
```

Do not assume the summary in this BRD is more current than the repository. Record material differences in the final builder report.

---

# 1. Why This Is the Next Build

Commit `5f8565d` added the first credible Phase 3 implementation slice:

- pack lifecycle and namespaces;
- dependency validation and resource limits;
- core-guarantee activation gates;
- typed evidence and conflicts;
- deterministic activation recommendations;
- `DO_NOT_ACTIVATE` and economics;
- protocol drift detection;
- a synthetic Retail reference environment;
- transaction replay, cancellation, receipts, and unknown-outcome representation;
- passing unit, regression, mutation, packaging, and CLI checks.

The remaining blockers are not cosmetic. They define whether Agent Native is a trustworthy system or a sophisticated in-memory demonstration.

The next build MUST address:

1. independent Phase 2C evidence;
2. production-safe core-guarantee attestations;
3. pack signing and dependency trust;
4. durable transactional state and crash recovery;
5. connector/environment isolation;
6. expanded property, fuzz, concurrency, and mutation verification;
7. complete Retail return/refund/payment-boundary simulation;
8. independent Phase 3A and 3B re-audit readiness.

Adding another sector before these close would increase surface area without increasing credibility.

---

# 2. RC1 Outcomes

RC1 MUST demonstrate that:

1. transactional packs activate only from independently verifiable core evidence;
2. test-only guarantee fixtures cannot enable non-test execution;
3. pack and dependency integrity are rooted in an explicit trust policy;
4. retries and unknown outcomes remain safe across process restarts;
5. connector calls are bound to tenant, environment, endpoint, credential class, and permitted side-effect mode;
6. a sandbox connector cannot silently reach production;
7. Retail purchase, cancellation, return, refund, and payment-authorization states have explicit authority and idempotency boundaries;
8. property, state-machine, fuzz, concurrency, and mutation tests validate invariants rather than examples alone;
9. installed artifacts behave the same as the source checkout;
10. immutable evidence is ready for independent Phase 3A and Phase 3B audits.

---

# 3. Scope

## 3.1 In scope

- Phase 2C final independent re-audit orchestration and evidence ingestion.
- Core guarantee attestation model and trust-store enforcement.
- Removal or strict confinement of `CoreGuaranteeRegistry.for_test()`.
- Pack signing, verification, key rotation, revocation, and dependency lock policy.
- Durable reference persistence for transaction, confirmation, receipt, Retail order, pack state, and evidence state.
- Crash recovery and reconciliation.
- Generic connector contract and environment policy.
- Deterministic local/sandbox Retail connector reference implementation.
- SSRF, endpoint, credential, tenant, environment, and side-effect boundary controls.
- Retail payment-authorization simulator.
- Retail return and refund state machines.
- Expanded property, state-machine, fuzz, concurrency, failure-injection, and mutation suites.
- Recommendation benchmark expansion.
- Clean-package, installed-wheel, restart, and audit evidence.

## 3.2 Out of scope

RC1 MUST NOT:

- process real card data;
- connect to a production payment processor;
- accept production merchant credentials;
- claim UCP, ACP, A2A, MCP, payment-network, or platform certification;
- build full Shopify, Stripe, EHR, scheduling, or marketplace integrations;
- production-harden the Healthcare Administration or Local Business packs;
- replace the canonical v2 identity, delegation, policy, confirmation, transaction, receipt, or tracing models;
- rely on a cloud KMS, HSM, or managed database to pass the reference implementation;
- convert an independent audit into a builder-owned self-review.

---

# 4. Required Delivery Order

The work MUST proceed in this order:

```text
Gate 0  Phase 2C independent re-audit
  ↓
Gate 1  Core guarantee attestation and trust enforcement
  ↓
Gate 2  Pack signing and dependency trust
  ↓
Gate 3  Durable state and crash recovery
  ↓
Gate 4  Connector and environment boundary
  ↓
Gate 5  Retail return/refund/payment boundary
  ↓
Gate 6  Expanded adversarial verification
  ↓
Gate 7  Phase 3A/3B independent audit handoff
```

Code preparation for a later gate MAY occur in parallel only when it cannot bypass or obscure an earlier gate.

---

# 5. Workstream 0 — Phase 2C Final Independent Re-Audit

## RC1-AUD-001 — Fresh independent reviewer — MUST

The Phase 2C re-audit MUST use a fresh reviewer/session that did not implement the remediation.

## RC1-AUD-002 — Immutable audit iteration — MUST

Create a new immutable evidence folder, following the existing naming convention, such as:

```text
audit_v2/phase2c/rerun_02/
```

Do not modify prior audit folders.

## RC1-AUD-003 — Reproduce original HIGH findings first — MUST

The auditor MUST first attempt:

```text
same key + changed principal
same key + changed agent
same key + changed environment
completed confirmed same-key retry
lost response followed by same transaction retry
```

Expected:

```text
changed material identity → conflict / no prior-result disclosure
same completed logical transaction → prior result replayed
no second confirmation consumption
no second side effect
```

## RC1-AUD-004 — Broader regression — MUST

The reviewer MUST rerun identity, delegation, policy, confirmation, quote, TOCTOU, risk ceiling, atomic idempotency, unknown outcome, receipt, trace, redaction, packaging, and mutation gates.

## RC1-AUD-005 — Gate artifact — MUST

The result MUST produce a machine-readable guarantee artifact only if the audit passes. The builder MUST NOT hand-author a passing guarantee.

Required status:

```text
PHASE_2C_READY
```

or:

```text
PHASE_2C_NOT_READY
```

If `NOT_READY`, stop transactional Phase 3 promotion and remediate before continuing to final audit.

---

# 6. Workstream 1 — Core Guarantee Attestation

The current `CoreGuaranteeRegistry.for_test()` fixture is appropriate for unit tests but MUST NOT become a release bypass.

## RC1-GATE-001 — Signed guarantee attestation — MUST

Define a canonical `CoreGuaranteeAttestation`:

```yaml
attestation_id:
schema_version:
subject:
  repository:
  commit_sha:
  package_version:
  core_content_hash:
guarantees:
  - guarantee_id:
    status: VERIFIED | FAILED | REVOKED | EXPIRED
    evidence_refs: []
audit:
  audit_run_id:
  auditor_id:
  issued_at:
  expires_at:
  toolchain_versions: {}
signature:
  algorithm:
  key_id:
  value:
```

## RC1-GATE-002 — Exact subject binding — MUST

An attestation MUST bind the exact commit/package/core hash reviewed. Evidence for one build MUST NOT activate a different build.

## RC1-GATE-003 — Trust-store verification — MUST

The production-capable registry MUST accept attestations only when:

- schema is supported;
- subject matches the running build;
- required guarantee is `VERIFIED`;
- evidence references are present and integrity-checkable;
- attestation is not expired or revoked;
- signing key is trusted for the environment;
- signature verifies over canonical content.

## RC1-GATE-004 — Test-fixture confinement — MUST

`CoreGuaranteeRegistry.for_test()` MUST be moved to a clearly test-only module or protected by an explicit test-environment invariant.

It MUST fail if used when any of the following indicate non-test execution:

- production/staging environment;
- installed CLI activation path;
- connector side effects enabled;
- non-test trust policy;
- missing explicit test marker.

The installed production package SHOULD omit the test fixture where practical.

## RC1-GATE-005 — No environment-variable bypass — MUST

A single environment variable, CLI flag, or unsigned local file MUST NOT mark a core guarantee verified.

## RC1-GATE-006 — Revocation — MUST

Revoking an attestation MUST prevent new transactional activation. Historical receipts MUST remain verifiable and identify the attestation that was active at execution time.

## RC1-GATE-007 — CLI inspection — MUST

Add machine-readable inspection commands or equivalent public APIs:

```text
agentnative guarantees list
agentnative guarantees verify <attestation>
agentnative guarantees status
```

Inspection MUST NOT mutate trust state.

---

# 7. Workstream 2 — Pack Signing and Dependency Trust

## RC1-SIGN-001 — Canonical signed payload — MUST

Sign a canonical envelope containing at minimum:

```yaml
pack_id:
pack_version:
pack_schema_version:
content_hash:
core_version_requirement:
required_core_guarantees: []
dependency_lock_hash:
effective_at:
sunset_at:
```

Do not sign raw YAML bytes whose whitespace or key order may change without semantic change.

## RC1-SIGN-002 — Maintained cryptography — MUST

Use a maintained cryptographic library and an approved asymmetric signing algorithm consistent with the project's existing security design. Do not implement cryptographic primitives manually.

## RC1-SIGN-003 — Trust policy — MUST

Define environment-specific policy:

```yaml
environment:
required_signatures:
trusted_publishers: []
trusted_key_ids: []
allowed_algorithms: []
allow_unsigned_seed_packs:
```

Production-capable transactional activation MUST require signatures.

## RC1-SIGN-004 — Key lifecycle — MUST

Support:

- key creation metadata;
- activation date;
- expiration;
- rotation;
- revocation;
- replacement key linkage;
- compromised-key emergency denial.

Private-key storage and remote signing are out of scope, but the interface MUST not require private keys inside the repository.

## RC1-SIGN-005 — Dependency lock — MUST

Create a deterministic dependency lock for:

- pack dependencies;
- protocol adapters;
- connectors;
- runtime packages material to pack behavior;
- expected versions and hashes.

Undeclared or changed material dependencies MUST fail activation or require an explicit upgrade review.

## RC1-SIGN-006 — Dependency graph validation — MUST

Detect:

- cycles;
- missing dependency;
- incompatible version;
- duplicate provider;
- revoked dependency;
- signed parent referencing unsigned required child;
- dependency hash mismatch;
- downgrade to a vulnerable/revoked version.

## RC1-SIGN-007 — Upgrade impact binding — MUST

The existing upgrade-impact report MUST include signature/trust changes, dependency-lock changes, and newly required core guarantees.

## RC1-SIGN-008 — Historical verification — MUST

Previously generated recommendations, blueprints, traces, and receipts MUST retain the pack hash and signing-key reference required to verify historical context after rotation or deprecation.

---

# 8. Workstream 3 — Durable State and Crash Recovery

The current Retail environment and transaction stores are process-local. RC1 MUST add a durable reference implementation.

## RC1-STORE-001 — Repository interfaces — MUST

Define stable storage interfaces for:

- idempotency records;
- logical transactions;
- confirmation bindings;
- receipts;
- Retail orders and state transitions;
- reconciliation tasks;
- pack lifecycle state;
- evidence observations;
- guarantee attestations and revocations.

Core business logic MUST depend on interfaces rather than a concrete database.

## RC1-STORE-002 — Durable local reference backend — MUST

Implement a transactional local reference backend suitable for repeatable tests and demonstrations. SQLite is preferred unless the repository already defines another durable reference standard.

## RC1-STORE-003 — Atomic transaction boundary — MUST

Where logically required, persist atomically:

```text
idempotency claim
logical transaction state
confirmation binding
business outcome reference
canonical receipt reference
```

If the downstream side effect cannot share the same transaction, represent the ambiguity explicitly with an outbox/reconciliation pattern or documented equivalent.

## RC1-STORE-004 — Restart safety — MUST

After process restart:

- completed same-key retries return the existing outcome;
- pending transactions do not execute blindly;
- unknown outcomes enter verification/reconciliation;
- confirmation remains bound to the same logical transaction;
- a different transaction cannot reuse the confirmation;
- receipts remain verifiable;
- pack and attestation context remains available.

## RC1-STORE-005 — State transition integrity — MUST

Persist Retail state transitions as append-only events or an equivalent auditable transition record. Invalid or out-of-order transitions MUST be rejected.

## RC1-STORE-006 — Concurrency control — MUST

Use database constraints, compare-and-set/versioning, locking, or an equivalent mechanism to guarantee:

- one idempotency owner;
- one confirmation owner per logical transaction;
- no double inventory decrement;
- no duplicate order/refund side effect;
- no lost terminal state.

Process-local locks alone do not satisfy this requirement.

## RC1-STORE-007 — Migration discipline — MUST

Storage schema changes MUST be versioned and tested for:

- clean creation;
- forward migration;
- interrupted migration;
- unsupported downgrade;
- data preservation;
- historical receipt verification.

## RC1-STORE-008 — Reconciliation queue — MUST

Unknown outcomes MUST create durable reconciliation work containing:

```yaml
reconciliation_id:
logical_transaction_id:
downstream_reference:
reason:
verification_strategy:
attempt_count:
next_attempt_at:
status:
evidence_refs: []
```

No automatic retry may create a second business side effect without safe downstream verification.

---

# 9. Workstream 4 — Connector and Environment Boundary

## RC1-CONN-001 — Canonical connector contract — MUST

Define:

```python
discover_capabilities()
test_connection()
read_configuration()
read_resource()
prepare_action()
execute_action()
verify_action()
compensate_action()
normalize_result()
emit_trace()
```

Not every connector must support every method. Unsupported operations MUST be explicit.

## RC1-CONN-002 — Connector binding — MUST

Every connector instance MUST bind:

```yaml
connector_id:
connector_version:
tenant_id:
business_id:
environment:
endpoint_allowlist: []
credential_reference:
credential_class:
network_policy:
permitted_capabilities: []
side_effect_mode: READ_ONLY | SIMULATED | SANDBOX_MUTATION | PRODUCTION_MUTATION
```

## RC1-CONN-003 — Environment policy — MUST

The policy engine MUST reject:

- sandbox credential with production endpoint;
- production credential in simulation;
- environment mismatch with transaction context;
- unallowlisted host or port;
- insecure scheme where HTTPS is required;
- mutation when side-effect mode is read-only/simulated;
- connector version not allowed by the active pack lock.

## RC1-CONN-004 — Credential boundary — MUST

The connector receives a credential reference, not a secret embedded in a pack, request, trace, receipt, or recommendation. Secret retrieval MUST occur through an injectable secret-provider interface.

The reference implementation MAY use an in-memory test provider but MUST prevent secret serialization.

## RC1-CONN-005 — SSRF and redirect defense — MUST

Connector HTTP policy MUST account for:

- loopback/link-local/private network targets according to policy;
- DNS rebinding risk;
- redirect to an unallowlisted host;
- alternate schemes;
- embedded credentials in URLs;
- IPv4/IPv6 representation bypasses;
- user-controlled callback URLs.

## RC1-CONN-006 — Reference Retail connector — MUST

Implement one deterministic local/sandbox Retail connector against a controlled fake merchant service. It MUST exercise the real connector boundary without requiring internet access or production credentials.

## RC1-CONN-007 — Capability truthfulness — MUST

A declared capability MUST be executable or clearly marked assessment-only. Metadata that looks complete while the executable operation is absent MUST fail anti-gaming tests.

## RC1-CONN-008 — Result normalization — MUST

Normalize downstream results into explicit states:

```text
SUCCEEDED
DENIED
FAILED_RETRYABLE
FAILED_TERMINAL
UNKNOWN_OUTCOME
PARTIAL
```

HTTP status alone MUST NOT determine business success.

## RC1-CONN-009 — Downstream verification — MUST

After an ambiguous mutation, `verify_action()` MUST be used before any retry when the downstream system supports verification.

## RC1-CONN-010 — Circuit breaker and bounded retry — SHOULD

The reference connector SHOULD implement bounded retry, backoff/jitter, timeout budgets, and circuit-breaker behavior for safe/read-only operations. Mutation retry MUST remain governed by transaction identity and downstream verification.

---

# 10. Workstream 5 — Retail Return, Refund, and Payment Boundary

## RC1-RET-001 — Separate capabilities — MUST

Model independently:

```text
check_return_eligibility
create_return_request
approve_return
receive_return
request_refund
execute_refund
get_refund_status
```

Purchase authority MUST NOT imply return or refund authority.

## RC1-RET-002 — Return state machine — MUST

Support at least:

```text
RETURN_NOT_REQUESTED
RETURN_ELIGIBLE
RETURN_INELIGIBLE
RETURN_REQUESTED
RETURN_AUTHORIZED
RETURN_REJECTED
RETURN_IN_TRANSIT
RETURN_RECEIVED
RETURN_INSPECTION_REQUIRED
RETURN_COMPLETED
```

## RC1-RET-003 — Refund state machine — MUST

Support at least:

```text
REFUND_NOT_REQUESTED
REFUND_REQUESTED
REFUND_AUTHORIZATION_PENDING
REFUND_AUTHORIZED
REFUND_REJECTED
REFUND_SUBMITTED
REFUND_PENDING
REFUNDED
REFUND_FAILED
REFUND_UNKNOWN_OUTCOME
REFUND_RECONCILIATION_REQUIRED
```

## RC1-RET-004 — Refund idempotency — MUST

Refund idempotency MUST be independent of purchase idempotency. Reusing a purchase key for refund MUST fail validation.

The refund fingerprint MUST bind:

- merchant/business;
- environment;
- principal;
- agent/provider;
- order and line-item identity;
- refund amount and currency;
- reason/category where material;
- return reference where required;
- confirmation identity;
- downstream payment reference.

## RC1-RET-005 — Refund ceilings — MUST

Refund amount MUST NOT exceed eligible captured/settled value minus prior successful refunds. Partial refunds MUST update remaining refundable value atomically.

## RC1-RET-006 — Payment authorization simulator — MUST

Create a simulator representing payment authorization without card data. It MUST support:

```text
AUTHORIZED
DECLINED
EXPIRED
REQUIRES_ACTION
TIMEOUT_UNKNOWN
REVERSED
```

Payment authorization is not an order and MUST NOT be treated as merchant acceptance.

## RC1-RET-007 — Separation of receipts — MUST

Maintain distinct correlated receipts for:

- purchase/order;
- cancellation;
- return authorization;
- refund.

A refund replay MUST return the original refund receipt and MUST NOT create a second refund receipt that resembles a new side effect.

## RC1-RET-008 — Compensation — MUST

If payment authorization succeeds but order creation fails, represent reversal/void or manual compensation requirements explicitly. Do not claim compensation succeeded without downstream evidence.

## RC1-RET-009 — Dispute evidence — SHOULD

Produce a dispute evidence bundle containing transaction, authority, quote, confirmation, order, return/refund, connector, receipt, and trace references without exposing sensitive payment information.

---

# 11. Workstream 6 — Expanded Verification

## 11.1 Property-based testing

Use a maintained property-testing framework or an equivalent reproducible generator.

Required domains:

- pack manifests and lifecycle sequences;
- dependency graphs;
- guarantee attestations;
- evidence records and conflicts;
- endpoint/environment combinations;
- transaction/confirmation identities;
- Retail state transitions;
- refund calculations;
- protocol-profile changes.

Required invariants:

```text
invalid input never partially activates
failed upgrade preserves last valid state
same logical transaction never produces two side effects
different material transaction never receives prior result
one confirmation binds at most one logical transaction
refund total never exceeds refundable value
disabled/revoked pack cannot execute new mutation
untrusted attestation cannot activate transactional pack
sandbox policy never permits production endpoint
unknown outcome never triggers blind mutation retry
```

## 11.2 Model-based state-machine testing

Generate Retail event sequences including:

- quote;
- expire;
- price change;
- inventory change;
- confirm;
- authorize payment;
- submit order;
- lose response;
- restart process;
- verify downstream;
- cancel;
- fulfill;
- return;
- refund;
- duplicate or reorder events.

Compare implementation state to a simple authoritative model after every action.

## 11.3 Fuzzing

Fuzz:

- YAML manifest parsing;
- canonical pack serialization;
- version requirements;
- dependency locks;
- signature envelopes;
- guarantee attestations;
- URLs and endpoint allowlists;
- connector results;
- protocol metadata;
- receipt verification inputs;
- reconciliation records.

Record corpus, seeds, time budget, crashes, hangs, and minimized counterexamples.

## 11.4 Concurrency

Run at minimum:

```text
8 workers × 25 rounds
```

for:

- same purchase transaction;
- competing purchases for final inventory;
- same confirmation with distinct transactions;
- duplicate cancellation;
- duplicate return request;
- duplicate refund;
- partial refunds against one order;
- pack activation/disable races;
- attestation revocation during activation;
- connector verification/retry race.

Use durable storage, not only in-memory fixtures.

## 11.5 Crash and restart testing

Terminate/reconstruct the process after each critical boundary:

```text
after idempotency claim
after confirmation binding
after payment authorization
after downstream order success
after local outcome persistence
after receipt creation
after refund downstream success
before response delivery
```

Expected results MUST be documented for every boundary.

## 11.6 Security negative testing

Required:

- unsigned pack under signature-required policy;
- valid signature from untrusted key;
- revoked signing key;
- signature copied to modified pack;
- dependency-lock tampering;
- audit attestation for a different commit;
- expired/revoked attestation;
- test fixture used outside test mode;
- cross-tenant credential reference;
- sandbox-to-production endpoint substitution;
- redirect to forbidden host;
- IPv4/IPv6 allowlist bypass;
- secret in error/trace/receipt;
- production mutation through read-only connector mode.

## 11.7 Recommendation benchmark expansion

Expand the seed benchmark to include:

- trustworthy direct path;
- platform-mediated preference;
- human handoff preference;
- `DO_NOT_ACTIVATE` for risk;
- `DO_NOT_ACTIVATE` for economics;
- stale/conflicting evidence;
- untrusted connector;
- missing operational capacity;
- protocol drift invalidating prior readiness;
- signed pack with unverified core guarantee;
- verified core with unsigned transactional pack.

Mandatory high-risk denial cases MUST pass 100%.

## 11.8 Mutation expansion

Add production-sensitive mutations for at least:

```text
M-GATE-ALLOW-TEST-FIXTURE
M-GATE-IGNORE-SUBJECT-HASH
M-GATE-IGNORE-REVOCATION
M-SIGN-SKIP-VERIFY
M-SIGN-TRUST-ANY-KEY
M-DEPS-IGNORE-LOCK
M-STORE-NONATOMIC-IDEMPOTENCY
M-STORE-DROP-CONFIRMATION-BINDING
M-STORE-BLIND-UNKNOWN-RETRY
M-CONN-SKIP-ENVIRONMENT
M-CONN-SKIP-ENDPOINT-ALLOWLIST
M-CONN-LEAK-CREDENTIAL
M-RET-DUPLICATE-REFUND
M-RET-EXCEED-REFUNDABLE
M-RET-PURCHASE-AUTH-IMPLIES-REFUND
```

Every critical mutation MUST be caught by the ordinary maintained suite.

---

# 12. Audit Evidence Requirements

## RC1-EVID-001 — Evidence manifest — MUST

Every build/audit run MUST produce a machine-readable evidence manifest:

```yaml
run_id:
repository:
commit_sha:
package_version:
python_version:
dependency_lock_hash:
started_at:
completed_at:
commands: []
results:
  tests:
  subtests:
  property_cases:
  fuzz_cases:
  concurrency_rounds:
  mutations_killed:
  mutations_survived:
  package_checks:
artifacts: []
artifact_hashes: {}
status:
```

## RC1-EVID-002 — Immutable separation — MUST

Builder evidence and independent audit evidence MUST be stored separately. The builder MUST NOT overwrite auditor output.

## RC1-EVID-003 — Reproduction — MUST

The independent reviewer MUST be able to reproduce the critical suite from documented commands in a clean environment.

## RC1-EVID-004 — Installed artifact evidence — MUST

Critical activation, signature, attestation, connector, restart, purchase, and refund tests MUST run against the installed wheel, not only source imports.

## RC1-EVID-005 — Failure preservation — MUST

Do not delete or rewrite failed audit results after remediation. Create a new iteration and link it to the prior finding.

---

# 13. Clean Package and CI Requirements

CI MUST include separate jobs for:

```text
lint/type/static checks if maintained
unit and regression tests
property/state-machine tests
fuzz smoke corpus
concurrency/restart tests
mutation checks
wheel build and metadata validation
installed-wheel smoke
security negative tests
traceability validation
```

The pipeline MUST:

- pin or lock build dependencies;
- expose exact test counts;
- fail on skipped critical gates unless explicitly approved and documented;
- preserve evidence artifacts;
- avoid repository secrets in fork/untrusted execution;
- test the minimum and primary supported Python versions where declared;
- prevent test-only fixtures from being accepted as release evidence.

---

# 14. RC1 Exit Gates

## 14.1 Phase 3A builder exit

Phase 3A may become:

```text
READY_FOR_PHASE_3A_INDEPENDENT_REVIEW
```

only when:

- Phase 2C is independently `READY` for the exact subject build or its accepted inherited core build;
- guarantee attestations verify exact subject, evidence, signature, trust, expiry, and revocation;
- test fixtures cannot activate non-test execution;
- signed pack and dependency policy passes positive and negative tests;
- lifecycle, disablement, revocation, and historical verification remain correct;
- property, fuzz, concurrency, restart, mutation, clean-wheel, and CI evidence passes;
- no open HIGH or CRITICAL builder finding remains.

## 14.2 Phase 3B builder exit

Phase 3B may become:

```text
READY_FOR_PHASE_3B_INDEPENDENT_REVIEW
```

only when:

- Phase 3A is independently ready or the independent review is explicitly structured as a combined gate;
- durable purchase/replay/unknown-outcome behavior passes restart tests;
- connector environment/credential/endpoint/side-effect boundaries pass;
- the controlled Retail connector exercises real boundary code;
- purchase, cancellation, return, refund, and payment-authorization states are explicit;
- refund authority, ceiling, idempotency, and receipt separation pass;
- no blind retry occurs after ambiguous downstream mutation;
- required security, concurrency, state-machine, mutation, package, and audit-evidence gates pass;
- no open HIGH or CRITICAL builder finding remains.

## 14.3 Independent status

Only the independent reviewer may declare:

```text
PHASE_3A_READY
PHASE_3B_READY
```

---

# 15. Required Deliverables

RC1 MUST create or update:

1. `V3/PHASE_3_RC1_BUILD_REPORT.md`
2. `V3/REQUIREMENTS_TRACEABILITY.md`
3. Core guarantee attestation schema and verifier.
4. Test-only fixture confinement documentation.
5. Pack signing and dependency-lock specification.
6. Key lifecycle and trust-policy ADR.
7. Durable storage architecture ADR.
8. Connector/environment boundary ADR.
9. Retail return/refund/payment-boundary ADR.
10. Updated Phase 3 architecture.
11. Updated threat-model delta.
12. Database schema/migrations and migration tests.
13. Controlled fake merchant service/reference connector.
14. Property/state-machine/fuzz/concurrency/restart test suites.
15. Expanded Phase 3 mutations.
16. Recommendation benchmark cases and results.
17. Machine-readable builder evidence manifest.
18. Clean-wheel verification report.
19. Independent Phase 3A audit handoff.
20. Independent Phase 3B audit handoff.

---

# 16. Suggested Commit Slices

Keep commits independently reviewable:

```text
1. add core guarantee attestation model and test-fixture confinement
2. add pack signing, trust policy, and dependency lock
3. add durable repositories and migrations
4. add restart-safe transaction and reconciliation flow
5. add connector/environment policy and controlled Retail connector
6. add Retail return/refund/payment state machines
7. add property, fuzz, concurrency, crash, and mutation coverage
8. update architecture, threat model, traceability, and builder evidence
```

Do not mix large documentation-only claims with unverified implementation in the same status change.

---

# 17. Builder Final Report Template

The final report MUST include:

## 1. Status

Exactly one builder status for Phase 3A and Phase 3B.

## 2. Baseline

Starting commit, branch, environment, and pre-existing failures.

## 3. Phase 2C gate

Independent audit result, audit iteration, exact subject, and evidence references.

## 4. Core guarantee attestations

Trust model, subject binding, expiration/revocation, fixture confinement, and negative tests.

## 5. Pack signing and dependencies

Canonical payload, verification, trust policy, key lifecycle, lockfile, and upgrade impact.

## 6. Durable state

Repository interfaces, backend, migrations, atomicity, restart behavior, and reconciliation.

## 7. Connector boundary

Environment binding, endpoints, credentials, network policy, side effects, and controlled reference connector.

## 8. Retail completion

Purchase, cancellation, return, refund, payment authorization, receipts, and recovery.

## 9. Verification

Exact counts for unit, regression, property, state-machine, fuzz, concurrency, crash, security-negative, mutation, and installed-wheel tests.

## 10. Audit evidence

Evidence-manifest path, hashes, immutable audit handoff, and reproduction commands.

## 11. Requirement traceability

Every RC1 requirement mapped to code, test, evidence, and status.

## 12. Residual risks

Explicit limitations, severity, owner, and release effect.

---

# 18. Definition of Done

RC1 is done only when the following statement is true:

> Agent Native can prove that a specifically audited core build authorized a specifically signed sector pack and locked dependency set; the pack can execute a controlled Retail journey only through a tenant- and environment-bound connector; transaction, confirmation, order, return, refund, receipt, and reconciliation state survive process restart; ambiguous downstream outcomes never trigger blind duplicate mutations; and independent reviewers can reproduce the evidence from the installed package.

Anything less remains a strong prototype, not a release candidate.

---

# 19. Portfolio Standard

This build should demonstrate principal-level systems judgment through:

- explicit trust roots;
- subject-bound audit evidence;
- durable distributed-systems semantics;
- crash and concurrency reasoning;
- secure connector boundaries;
- separation of purchase, return, refund, and payment authority;
- model-based and adversarial evaluation;
- honest release governance.

The next impressive feature is not another pack.

The next impressive feature is proof that the platform still behaves correctly when processes crash, networks lie, credentials are wrong, keys are revoked, requests race, and money might have moved.

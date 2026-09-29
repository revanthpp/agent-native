# Agent Native v3 — Phase 3B Closure and Remediation BRD

## Resolve Product Integrity, Simulation Fidelity, Durability, Evidence, and Release-Gate Issues

**Document status:** AUTHORITATIVE NEXT REMEDIATION BUILD  
**Version:** 1.0  
**Date:** 2026-09-28  
**Repository:** `revanthpp/agent-native`  
**Target branch:** `feature/phase3-sector-packs`  
**Reviewed commit:** `1c6a796d99adb81464a66a4773c59dbb8ba6ba6e`  
**Required outcome:** `READY_FOR_PHASE_3B_INDEPENDENT_REVIEW`

---

# 0. Direction to Codex

Perform one bounded Phase 3B closure build. Resolve every requirement in this document; do not add new sectors, a hosted UI, real credentials, or unrelated features.

The current workflow is a credible product-review prototype, but its verification is shallower than several claims in the build report. Green regression counts do not close the issues below.

The build MUST:

1. replace simulated labels with behaviorally faithful scenarios;
2. fail closed on unsupported, malformed, incomplete, or contradictory inputs;
3. bind recommendations to actual journey capabilities, policies, protocols, and evidence;
4. prove restart and concurrency safety for value-changing operations;
5. produce evidence tied unambiguously to the exact source commit and CI run;
6. reconcile status documents without overstating independent readiness; and
7. generate an audit-ready handoff for an independent reviewer.

No listed requirement may be waived, marked “future,” or closed only through documentation. If a requirement cannot be implemented, the final status MUST remain `PHASE_3B_REMEDIATION_INCOMPLETE` with the blocker identified.

---

# 1. Review Verdict

The current status `READY_FOR_PHASE_3B_PRODUCT_REVIEW` is acceptable only as a narrow synthetic-demo status. It is not sufficient as a closure status.

## 1.1 Material findings

| ID | Severity | Finding | Required disposition |
|---|---:|---|---|
| F-01 | Critical | Unknown scenario names silently execute the happy path. Template scenarios such as `deceptive` and `malformed` are not implemented. | Reject unknown scenarios and implement every advertised scenario. |
| F-02 | High | `lost-response` stops at `UNKNOWN_OUTCOME`; it does not demonstrate retry, reconciliation, or singular side effect. | Execute and prove the complete recovery path. |
| F-03 | High | `expired-delegation` is an unknown-agent denial with an appended label rather than an expired delegation. | Model and validate actual delegation expiry. |
| F-04 | High | `connector-outage` executes the same payment-timeout path as `payment-unknown`; no connector outage occurs. | Inject a real connector failure and verify bounded behavior. |
| F-05 | Critical | Activation recommendations are not gated by the capabilities required by each journey. A retailer can receive `DIRECT` despite missing executable capabilities. | Add explicit journey-readiness gates and fail-closed recommendation rules. |
| F-06 | High | `policy_profile`, protocol requirements, capability evidence, and platform inventory are mostly reported rather than enforced in the recommendation. | Make them decision inputs with evidence-backed reason codes. |
| F-07 | High | Workspace validation checks only a small part of the schema; malformed nested records can cause `KeyError`, misleading results, or late crashes. | Add strict versioned schema validation and stable validation errors. |
| F-08 | High | Capability states can be self-declared as tested/executable without independent evidence binding. | Require evidence references and provenance for readiness-bearing states. |
| F-09 | Critical | SQLite persists orders but not payment authorizations, returns, or refunds. Restart replay can dereference missing in-memory state. | Persist and reload all value-changing entities and transitions. |
| F-10 | Critical | Idempotency claim, inventory mutation, order persistence, receipt attachment, and events are separate writes. Crash windows can leave partial state. | Introduce atomic unit-of-work semantics or durable recovery invariants. |
| F-11 | High | Lost-response state differs between memory and persisted order state; replay semantics are ambiguous. | Define and test authoritative downstream state vs delivery state. |
| F-12 | High | Refund/payment unknown outcomes lack complete restart-safe reconciliation and terminal resolution tests. | Implement and prove reconciliation state machines. |
| F-13 | High | Product tests contain only four broad tests; directionality checks merely require an expected pattern to appear somewhere. | Add exact journey-level assertions, negative tests, and mutation tests. |
| F-14 | High | CI smoke commands run after an editable install and do not isolate the installed wheel workflow. | Run product smoke tests exclusively in a clean wheel-only environment. |
| F-15 | High | The committed evidence manifest names a parent source commit while the repository head contains a later evidence commit; source, evidence, CI run, and artifact identity are not explicit. | Use a non-self-referential provenance model with source SHA and evidence SHA/run identity. |
| F-16 | Medium | No pull-request workflow run was associated with the reviewed commit through the available repository evidence. | Require a successful CI run and record its immutable URL/ID and artifact digest. |
| F-17 | Medium | `retail init` can overwrite an existing `project.yaml` without an explicit force option. | Refuse overwrite by default; add `--force` with clear warning. |
| F-18 | Medium | Blueprint and evidence writes are not atomic and may leave partial files. | Write to a temporary file, fsync where supported, and atomically replace. |
| F-19 | Medium | Global `random.seed()` mutates process-wide state and is unnecessary for current scenarios. | Use a local RNG or remove randomness. |
| F-20 | Medium | Project hashes deliberately remove broad keys such as `integrity`, which can hide material changes. | Define a narrow, versioned canonicalization policy and test every excluded field. |
| F-21 | Medium | Protocol readiness trusts workspace-provided status strings and fixed fixture hashes without verifying artifacts. | Verify fixture/profile hash and compatibility or report `UNVERIFIED`. |
| F-22 | Medium | Reports contain split Phase 3B terminology (`PHASE_3B_NOT_READY` infrastructure vs product review ready) that can confuse users. | Publish one status taxonomy with scope and authority. |
| F-23 | Medium | Phase 2C remains independently `PHASE_2C_NOT_READY`; builder remediation cannot self-promote it. | Produce a new independent re-audit handoff and preserve the independent boundary. |

---

# 2. Scope

## 2.1 In scope

- Retail workspace schema and validation
- Journey/capability/policy/protocol/evidence gating
- All advertised synthetic simulation scenarios
- Durable order, payment, return, refund, receipt, event, and reconciliation state
- Concurrency, crash, restart, retry, and idempotency behavior
- CLI safety and output integrity
- Evidence provenance, CI, mutation testing, traceability, and status reconciliation
- Independent Phase 2C and Phase 3B review handoff packages

## 2.2 Out of scope

- Real merchant or payment credentials
- Production payment capture
- Live production connectors
- Hosted web UI
- Healthcare or small-business sector packs
- Claims of protocol certification
- Enterprise KMS/HSM implementation

Out-of-scope items MUST remain documented boundaries. They MUST NOT be presented as implemented or tested.

---

# 3. Functional Requirements

## 3.1 Versioned workspace schema

### P3B-REM-SCHEMA-001 — Canonical schema

Define a machine-readable JSON Schema for `project.yaml`. YAML input MUST be validated against the schema before domain objects are constructed.

### P3B-REM-SCHEMA-002 — Strict nested validation

Validate all required fields, types, enums, formats, ranges, uniqueness rules, and cross-field constraints for:

- project identity and version;
- business and tenant identity;
- business profile and economics;
- platforms and capabilities;
- protocol profiles;
- evidence sources;
- policies;
- priority journeys; and
- simulation configuration.

Unknown fields MUST be rejected by default or preserved only through an explicit versioned extension namespace.

### P3B-REM-SCHEMA-003 — Semantic constraints

At minimum enforce:

- nonempty stable IDs;
- unique capability, protocol, evidence, and journey IDs;
- finite, nonnegative money values;
- supported ISO currency codes used consistently;
- confidence in `[0, 1]`;
- timezone-aware evidence timestamps;
- no impossible or future evidence timestamps beyond a documented skew;
- positive inventory and volume rules where applicable;
- known capability and evidence states;
- valid environment/pack/version combinations; and
- required protocol profiles for selected journeys.

### P3B-REM-SCHEMA-004 — Stable error contract

Validation failures MUST return structured errors containing `code`, `json_path`, `message`, and `remediation`. No malformed user input may escape as `KeyError`, traceback, or generic internal error.

### P3B-REM-SCHEMA-005 — Workspace migration

Reject unsupported workspace versions with a clear migration instruction. Add an explicit migration function or CLI command for any supported prior version.

### P3B-REM-SCHEMA-006 — Safe initialization

`retail init` MUST refuse to overwrite an existing workspace. `--force` MUST be explicit, preserve or back up the prior file, and be tested.

---

## 3.2 Evidence-backed readiness

### P3B-REM-EVID-001 — Evidence-bound capability states

`TESTED`, `EXECUTABLE_IN_SIMULATION`, and `EXECUTABLE_IN_SANDBOX` MUST require one or more resolvable evidence references containing provenance, environment, timestamp, collector, result, and artifact hash.

### P3B-REM-EVID-002 — Anti-self-attestation

A business-profile declaration alone MUST NOT promote a capability beyond `DECLARED`. Missing, stale, conflicting, or unverifiable evidence MUST downgrade readiness and produce an explicit gap.

### P3B-REM-EVID-003 — Freshness and conflicts

Define freshness windows by evidence type. Conflicting observations MUST not be resolved by ordering or confidence alone unless a documented deterministic adjudication policy applies.

### P3B-REM-EVID-004 — Protocol verification

Protocol readiness MUST be calculated from verified local fixtures or artifacts. Recompute and compare `source_hash`; reject a mismatch. Workspace-supplied compatibility text MUST be treated as a claim, not a verified result.

### P3B-REM-EVID-005 — Secret and privacy safety

Run secret detection and sensitive-data redaction over inputs, generated blueprints, evidence bundles, traces, exceptions, and CI artifacts. Add adversarial tests for encoded, nested, key-name, bearer-token, credential-assignment, and multiline variants.

---

## 3.3 Recommendation integrity

### P3B-REM-REC-001 — Journey prerequisites

Create a versioned prerequisite model per journey covering required capabilities, minimum capability state, policy controls, evidence, protocol profiles, identity, confirmation, payment, reversibility, handoff, and reconciliation.

### P3B-REM-REC-002 — Fail-closed gating

A recommendation MUST NOT be `DIRECT` or `PLATFORM_MEDIATED` when a required capability, authority, protocol control, or evidence item is unavailable. The engine MUST return the safest viable pattern or `DO_NOT_ACTIVATE` with machine-readable reason codes.

### P3B-REM-REC-003 — Policy enforcement

Use `policy_profile` as an enforced decision input. Requirements such as confirmation, human approval, refund ceiling, risk tolerance, and handoff availability MUST alter the recommendation and simulation behavior.

### P3B-REM-REC-004 — Exact portfolio decision

Return both journey-level decisions and one deterministic portfolio-level decision. Define precedence: `DO_NOT_ACTIVATE` for a critical value-changing journey MUST not be hidden by a low-risk journey that is `DIRECT`.

### P3B-REM-REC-005 — Explainability

Every decision MUST contain:

- satisfied prerequisites;
- blocking prerequisites;
- evidence references and verification status;
- applied policy rules;
- unit economics;
- assumptions and unknowns;
- residual risks;
- viable alternatives; and
- deterministic reason codes.

### P3B-REM-REC-006 — Sensitivity tests

Add tests proving that one material input change changes only the expected decision dimensions. Include capability removal, evidence expiry, protocol hash drift, lower margin, no handoff capacity, higher reversibility, and stricter confirmation policy.

---

## 3.4 Simulation fidelity

### P3B-REM-SIM-001 — Scenario registry

Create a single typed registry of supported scenario IDs. Journey templates, CLI choices/help, tests, and implementation MUST derive from this registry.

### P3B-REM-SIM-002 — Unknown scenario rejection

Unknown or misspelled scenario IDs MUST exit nonzero with `UNKNOWN_SCENARIO`. They MUST never fall through to happy path.

### P3B-REM-SIM-003 — Complete advertised coverage

Implement every scenario advertised by a journey or report, including positive, deceptive, malformed, stale inventory, price change, expired quote, unknown agent, expired delegation, lost response, duplicate retry, cancellation race, payment unknown, duplicate refund, refund ceiling, connector outage, and human handoff.

### P3B-REM-SIM-004 — Behavioral truth

Each scenario MUST trigger the named control through its actual domain mechanism. Adding a finding label after a different failure is prohibited.

### P3B-REM-SIM-005 — Lost-response recovery

The scenario MUST show:

1. side effect committed once;
2. response lost;
3. client retry with the same identity;
4. no duplicate order;
5. reconciliation or verified replay;
6. terminal authoritative status; and
7. one receipt chain.

### P3B-REM-SIM-006 — Connector outage

Inject a connector-level unavailable/timeout result. Prove no unsafe retry, no fabricated success, bounded backoff metadata, and reconciliation/handoff as appropriate.

### P3B-REM-SIM-007 — Delegation expiry

Create a signed or otherwise domain-valid delegation that is expired at the deterministic clock. The denial MUST originate from delegation verification.

### P3B-REM-SIM-008 — Determinism and isolation

Use a local RNG instance only where randomness is necessary. Do not mutate global random state. Clocks, IDs, and fault injection MUST be dependency-injected and repeatable.

### P3B-REM-SIM-009 — Expected outcomes

Each scenario definition MUST state expected status, state transitions, side-effect count, receipts, reconciliation records, and findings. Test the entire contract—not merely that execution completes.

---

# 4. Durability and Transaction Requirements

## 4.1 Complete persistence

### P3B-REM-STORE-001

Persist and reload orders, inventory reservations or authoritative inventory effects, payment authorizations, returns, refunds, receipts, confirmations, idempotency records, events, and reconciliation work items.

### P3B-REM-STORE-002

Every persisted entity MUST include schema version, tenant/business/environment scope, created/updated timestamps, and optimistic concurrency version.

### P3B-REM-STORE-003

Add forward-only schema migrations and reject unsupported future schema versions.

## 4.2 Atomicity and crash safety

### P3B-REM-TXN-001

For each value-changing command, idempotency transition, domain state mutation, event, receipt reference, and reconciliation creation MUST occur in one database transaction where locally controlled.

### P3B-REM-TXN-002

Where an external side effect cannot share the transaction, use an explicit state machine and outbox/inbox or equivalent recovery pattern. Never infer failure from a missing response.

### P3B-REM-TXN-003

Define authoritative business state separately from response-delivery state. A lost response MUST not corrupt the authoritative order state.

### P3B-REM-TXN-004

Idempotency identity MUST bind key, request hash, tenant, business, environment, principal, agent/provider where applicable, capability, resource, amount/currency, quote, and confirmation/delegation references.

### P3B-REM-TXN-005

Retries with the same key and different material identity MUST fail closed. Same-identity retries MUST replay or reconcile without a duplicate side effect.

## 4.3 Concurrency

### P3B-REM-CONC-001

Prove exactly-once local effect under concurrent identical submissions from multiple threads and processes.

### P3B-REM-CONC-002

Prove bounded inventory under concurrent distinct purchases. Inventory MUST never become negative or oversell the configured quantity.

### P3B-REM-CONC-003

Prove cancellation-versus-fulfillment and return/refund races resolve through valid state transitions with one terminal outcome.

### P3B-REM-CONC-004

Prove aggregate refunds cannot exceed captured value under concurrent refund IDs and idempotency keys.

## 4.4 Restart and reconciliation

### P3B-REM-RECOV-001

Restart between every important transaction boundary and verify safe continuation. Include claim-before-effect, effect-before-record, record-before-receipt, unknown payment, unknown refund, and reconciliation completion.

### P3B-REM-RECOV-002

Reconciliation items MUST have stable IDs, owner/lease semantics, retry count, next attempt, terminal status, verification evidence, and audit history.

### P3B-REM-RECOV-003

Payment and refund unknown outcomes MUST support a verified transition to terminal success, terminal failure, or manual escalation without duplicate value movement.

---

# 5. CLI and Artifact Requirements

### P3B-REM-CLI-001

All commands MUST return documented exit codes and structured error codes. User errors return no traceback.

### P3B-REM-CLI-002

CLI scenario choices MUST be generated from the scenario registry and displayed by `--help`.

### P3B-REM-CLI-003

Blueprint and evidence output MUST use atomic writes. Existing files require explicit `--force` or a documented overwrite policy.

### P3B-REM-CLI-004

All commands MUST work from a clean wheel-only environment with no repository root, editable install, or `PYTHONPATH` available.

### P3B-REM-ART-001

Blueprints MUST distinguish `DECLARED`, `OBSERVED`, `TESTED`, `SIMULATED`, `SANDBOX_VERIFIED`, and `NOT_VERIFIED`. “Activate now” MUST be replaced by scope-accurate language when only simulation evidence exists.

### P3B-REM-ART-002

The evidence bundle MUST contain schema versions, canonicalization version, source commit, pack/engine versions and hashes, scenario definitions and outcomes, test manifest, CI identity, artifact digests, generation tool version, and explicit limitations.

### P3B-REM-ART-003

Canonicalization exclusions MUST be enumerated and narrowly justified. Material fields including integrity/provenance data MUST affect the relevant artifact hash.

---

# 6. Evidence and CI Provenance

### P3B-REM-PROV-001 — Two-commit evidence model

Avoid the impossible requirement for a commit to contain its own SHA. Record separately:

- `source_commit_sha`: the exact code/docs commit tested;
- `evidence_commit_sha`: the later commit that adds the immutable evidence manifest, if committed;
- CI repository, workflow, run ID, run attempt, event, runner image, and timestamps; and
- SHA-256 digest of every uploaded evidence artifact.

### P3B-REM-PROV-002 — Clean CI

CI MUST build from `source_commit_sha`, install only the wheel in a clean environment, execute the end-to-end Retail workflow, run all test and mutation gates, and upload evidence.

### P3B-REM-PROV-003 — Status checks

The reviewed commit MUST have a successful required status check. Local builder output alone is insufficient.

### P3B-REM-PROV-004 — Tamper evidence

The evidence manifest MUST be deterministic except for explicitly declared run metadata, contain artifact digests, and fail verification if a report, fixture, output, or manifest field is altered.

### P3B-REM-PROV-005 — No self-review claim

Builder-generated evidence MUST remain labeled `BUILDER_EVIDENCE_ONLY`. Independent audit status may change only through a separate reviewer-authored artifact.

---

# 7. Required Test Program

## 7.1 Schema and adversarial input tests

- missing and extra fields;
- wrong nested types;
- duplicate IDs;
- NaN/infinite/negative economics;
- invalid confidence and timestamps;
- YAML anchors, large nesting, and malformed documents;
- unknown states and versions;
- cross-tenant references;
- secret and encoded-secret variants; and
- unsupported scenarios.

## 7.2 Recommendation tests

- exact decision per journey for all four reference retailers;
- exact portfolio decision;
- missing required capability;
- declared-only capability;
- stale/conflicting evidence;
- protocol hash mismatch;
- confirmation/handoff policy changes;
- nonviable economics; and
- deterministic sensitivity matrix.

## 7.3 Scenario contract tests

Every registered scenario MUST have a positive contract test and at least one mutation that proves the named control matters. Registry coverage MUST fail if a journey advertises an unimplemented scenario.

## 7.4 Concurrency and crash tests

- thread and multiprocess identical-order races;
- last-item inventory contention;
- same/different idempotency identity races;
- cancellation/fulfillment race;
- duplicate and aggregate refund race;
- database busy/lock handling;
- kill/restart at injected transaction boundaries; and
- restart recovery for orders, payments, returns, refunds, receipts, and reconciliation.

Tests MUST use bounded timeouts and deterministic synchronization; timing-only sleeps are prohibited.

## 7.5 Property and state-machine tests

Add generated tests for:

- no duplicate value-changing side effect;
- inventory never below zero;
- refund total never above captured amount;
- invalid state transitions rejected;
- terminal states do not regress;
- same canonical input gives the same semantic result; and
- materially different identity cannot replay another result.

## 7.6 Packaging tests

Create a temporary clean virtual environment, install the built wheel, change working directory outside the repository, unset `PYTHONPATH`, and execute the documented under-ten-command demo plus negative CLI cases.

---

# 8. Mutation Requirements

Expand Phase 3 mutations beyond the current five. At minimum include mutations that:

1. restore unknown-scenario happy-path fallback;
2. ignore required capabilities;
3. accept declared-only capability readiness;
4. ignore stale/conflicting evidence;
5. skip protocol hash verification;
6. remove confirmation policy enforcement;
7. omit tenant/principal/environment from idempotency identity;
8. permit non-atomic order persistence;
9. allow inventory below zero;
10. allow aggregate over-refund;
11. retry an unknown external outcome blindly;
12. omit payment/refund restart loading;
13. label another failure as delegation expiry;
14. bypass output redaction; and
15. accept an evidence manifest for a different source commit.

Every mutation MUST be caught by a specifically named test. The report MUST map mutation → production control → detecting test.

---

# 9. Status and Documentation Reconciliation

### P3B-REM-STATUS-001

Publish one status vocabulary:

- `IMPLEMENTED`
- `BUILDER_VERIFIED`
- `READY_FOR_INDEPENDENT_REVIEW`
- `INDEPENDENTLY_VERIFIED`
- `PRODUCTION_READY`
- `BLOCKED`

Every status MUST include scope, authority, evidence reference, and date.

### P3B-REM-STATUS-002

Update README, build reports, traceability, architecture, threat model, ADRs, and evidence manifests to use the same status.

### P3B-REM-STATUS-003

Preserve Phase 2C as independently `NOT_READY` until a new independent rerun closes its historical blockers. Builder tests may establish remediation readiness but MUST NOT rewrite the independent verdict.

### P3B-REM-STATUS-004

Create two independent-review handoffs:

1. Phase 2C final rerun package covering all historical high-severity identity/replay issues; and
2. Phase 3B closure package covering this BRD.

---

# 10. Deliverables

The remediation commit MUST include:

1. versioned Retail workspace schema and migration support;
2. strict validator and structured error model;
3. journey prerequisite/readiness engine;
4. typed scenario registry and faithful scenario implementations;
5. complete durable data model and migrations;
6. atomic transaction/recovery implementation;
7. reconciliation worker or deterministic reference runner;
8. safe CLI and atomic artifact writes;
9. expanded tests and Phase 3 mutations;
10. clean wheel-only end-to-end script;
11. deterministic evidence manifest and verifier;
12. updated architecture, threat model, ADRs, traceability, README, and status files;
13. remediation build report; and
14. independent-review handoff packages.

---

# 11. Acceptance Gates

All gates are mandatory.

| Gate | Pass condition |
|---|---|
| G0 Scope | Every requirement ID maps to implementation and a test/evidence artifact. |
| G1 Schema | All malformed/adversarial workspaces fail closed with structured errors. |
| G2 Decisions | Exact journey and portfolio recommendations obey capability, evidence, policy, protocol, and economic gates. |
| G3 Scenarios | Every advertised scenario is implemented faithfully; unknown scenarios fail. |
| G4 Durability | All value-changing entities survive restart and reconcile correctly. |
| G5 Atomicity | Crash injection proves no duplicate order/refund and no unbounded partial state. |
| G6 Concurrency | Thread/process races preserve inventory, state-machine, and refund invariants. |
| G7 Security | Secret/redaction, tenant isolation, identity binding, and fail-closed tests pass. |
| G8 Mutations | All existing and newly required mutations are caught. |
| G9 Packaging | Wheel-only workflow passes outside the repository without editable imports. |
| G10 Provenance | Successful CI evidence is bound to the exact source commit and artifact digests verify. |
| G11 Documentation | Status and scope are consistent across all public artifacts. |
| G12 Handoff | Independent reviewer can reproduce the build from documented commands. |

The builder may declare only:

```text
READY_FOR_PHASE_3B_INDEPENDENT_REVIEW
```

The builder MUST NOT declare `INDEPENDENTLY_VERIFIED`, `PHASE_2C_READY`, or `PRODUCTION_READY`.

---

# 12. Required Final Report Format

The final response and build report MUST include:

1. source commit SHA and evidence commit SHA;
2. concise change summary by requirement group;
3. requirement-to-code-to-test traceability;
4. exact test, subtest, property, concurrency, crash, and mutation counts;
5. wheel-only demonstration result;
6. CI run identity and artifact digests;
7. independent handoff locations;
8. unresolved items, if any;
9. honest final status; and
10. GitHub branch/commit links.

If any acceptance gate fails, use:

```text
PHASE_3B_REMEDIATION_INCOMPLETE
```

No victory lap based solely on a larger pytest number. The proof must match the promise.

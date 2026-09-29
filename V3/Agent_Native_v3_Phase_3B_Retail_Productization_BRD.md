# Agent Native v3 — Phase 3B Retail Productization BRD
## Turn the Hardened Retail Reference System into a Useful End-to-End Product

**Document status:** AUTHORITATIVE NEXT BUILD
**Version:** 1.0
**Date:** 2026-09-29
**Target branch:** `feature/phase3-sector-packs`
**Reviewed baseline:** `2de0c62d9fe4404cfd417f4941a15d7318b4e722`
**Primary objective:** Complete Phase 3B Retail productization

---

# 0. Direction to Codex

The next build MUST move forward into Phase 3B Retail productization.

Do not perform additional Phase 2 feature work.

Phase 2C is engineering-complete for its documented synthetic scope. The repository still labels it `READY_FOR_PHASE_2C_FINAL_REAUDIT`, so a separate audit/status-reconciliation task remains, but that task MUST NOT consume the primary Phase 3 build stream.

The Phase 3 branch already contains:

- sector-pack lifecycle, provenance, signing, dependencies, and core gates;
- typed evidence and deterministic activation recommendations;
- protocol drift detection;
- durable SQLite transaction and Retail state;
- connector environment boundaries;
- purchase, cancellation, return, refund, payment-authorization, receipt, and reconciliation primitives;
- passing regression, mutation, packaging, and installed-wheel checks.

This build MUST make those capabilities usable as one coherent product journey.

---

# 1. Product Problem

The current implementation demonstrates strong components, but a user cannot yet easily answer:

```text
What should this retailer expose to agents?
Which participation model should it choose?
What is blocking activation?
Can I simulate the priority journey?
What failed and why?
What should the retailer build over the next 90 days?
```

Phase 3B must connect the components into a repeatable workflow that produces an evidence-backed Retail Activation Blueprint.

The product should feel like a decision and validation system—not a collection of security classes waiting patiently for a conference talk.

---

# 2. Phase 3B Product Outcome

A user MUST be able to:

1. create or load a Retail business profile;
2. describe business, technical, platform, risk, economic, and operating conditions;
3. inventory existing commerce capabilities and platforms;
4. select priority agent journeys;
5. receive an explainable activation recommendation;
6. view missing evidence, controls, dependencies, and protocol gaps;
7. simulate a controlled purchase lifecycle;
8. inject failures and observe recovery behavior;
9. generate a Retail Activation Blueprint and machine-readable evidence bundle;
10. receive a sequenced 30/60/90-day implementation plan;
11. reproduce the result from the same versioned inputs;
12. receive `DO_NOT_ACTIVATE` when activation is unjustified.

---

# 3. Scope

## 3.1 In scope

- Retail project/workspace model.
- Business and operating-profile intake.
- Retail journey portfolio.
- Capability and platform inventory.
- Activation recommendation workflow.
- Maturity and missing-gate assessment.
- Protocol/profile readiness reporting.
- Controlled end-to-end Retail simulation.
- Failure-injection presets.
- Blueprint, evidence bundle, and 30/60/90-day roadmap generation.
- CLI-first user experience with JSON and Markdown output.
- Example Retail businesses representing different activation strategies.
- Targeted critical concurrency/restart/refund tests.
- Documentation, quick start, walkthrough, and public-safe demo artifacts.

## 3.2 Not required in this build

- Production merchant credentials.
- Real card or bank data.
- Real payment execution.
- Production Shopify, Stripe, UCP, ACP, MCP, or A2A certification.
- Production DNS-rebinding/redirect enforcement for a live HTTP connector.
- Enterprise KMS/HSM operations.
- Exhaustive open-ended fuzzing.
- Healthcare or Local Business productization.
- A graphical web application.

These remain future productionization gates, not blockers to completing the synthetic Retail product.

---

# 4. Phase 2 Status Reconciliation — Separate Non-Blocking Task

## P3B-STATUS-001 — Verify canonical status — MUST

Inspect:

```text
PHASE_2C_RELEASE_REVIEW.md
V2/STATUS.md
README.md
audit_v2/phase2c/
audit_v2/phase2c/rerun_01/
```

## P3B-STATUS-002 — Do not invent a verdict — MUST

If no final independent artifact declares `PHASE_2C_READY`, preserve the accurate status but describe it as:

```text
Engineering complete; final independent status closure pending.
```

Do not describe it as active remediation or an ongoing build dependency.

## P3B-STATUS-003 — Continue Phase 3 — MUST

Phase 3 synthetic development MUST continue using the verified Phase 2 behavior and regression suites. Only a production-readiness claim depends on final independent status closure.

## P3B-STATUS-004 — Remove stale language — MUST

Update Phase 3 documents that incorrectly describe Phase 2C as an unresolved engineering blocker.

---

# 5. Retail Workspace Model

## P3B-WORK-001 — Project manifest — MUST

Define a versioned Retail workspace:

```yaml
project_id:
project_version:
business_id:
tenant_id:
name:
sector_pack:
pack_version:
created_at:
updated_at:
environment:
business_profile:
platform_inventory:
capability_inventory:
priority_journeys:
evidence_sources:
policy_profile:
simulation_profile:
```

## P3B-WORK-002 — Portable project directory — MUST

```text
retail-project/
  project.yaml
  evidence/
  fixtures/
  simulations/
  outputs/
```

The project MUST be portable and MUST NOT contain secrets.

## P3B-WORK-003 — Deterministic identity — MUST

Canonical inputs MUST produce a stable project/input hash. Generated timestamps and output paths MUST NOT alter decision identity.

## P3B-WORK-004 — Validation — MUST

Reject missing required fields, invalid enums, conflicting environments, unsupported pack versions, broken evidence references, and secret-like values in committed inputs.

---

# 6. Retail Business Profile

## P3B-PROFILE-001 — Required inputs — MUST

Capture business model, size, channels, product types, regulated categories, geographies, volume, average order value, margin, return rate, technical capacity, API maturity, existing platforms, identity/payment requirements, inventory freshness, human capacity, risk tolerance, agent-channel priority, and expected agent volume.

## P3B-PROFILE-002 — Evidence provenance — MUST

Each material input MUST support source, observation time, confidence, validity, and evidence reference using the existing typed evidence model.

## P3B-PROFILE-003 — Unknowns — MUST

Unknown or conflicting values remain visible. Do not assume mature APIs, fresh inventory, low risk, or available staff.

## P3B-PROFILE-004 — Minimize sensitive data — MUST

Use bands and references where precise financial, customer, credential, or payment data is unnecessary.

---

# 7. Retail Journey Portfolio

## P3B-JOURNEY-001 — Templates — MUST

Provide templates for:

1. product discovery;
2. product comparison;
3. inventory inquiry;
4. quote creation;
5. controlled checkout;
6. order-status retrieval;
7. cancellation;
8. return eligibility;
9. return request;
10. refund request/status;
11. customer-service handoff.

## P3B-JOURNEY-002 — Journey contract — MUST

Each journey declares persona, agent goal, business goal, capabilities, data, identity, principal authority, payment, confirmation, reversibility, human handoff, platform dependencies, protocol profiles, risk, economics, and evaluation scenarios.

## P3B-JOURNEY-003 — Prioritization — MUST

Show business value, customer value, feasibility, platform leverage, sensitivity, transaction risk, reversibility, operating burden, evidence completeness, and complexity. Do not collapse them into one opaque score.

## P3B-JOURNEY-004 — Lower autonomy may be success — MUST

A journey may succeed through discovery, read-only access, or human handoff. Maximum autonomy is not the default target.

---

# 8. Activation Decision Workflow

## P3B-ACT-001 — Patterns — MUST

For each journey generate:

```text
DIRECT
PLATFORM_MEDIATED
AGGREGATOR_MARKETPLACE
HUMAN_HANDOFF
DO_NOT_ACTIVATE
```

## P3B-ACT-002 — Explanation — MUST

Output the selected pattern, alternatives, rejected patterns, evidence, assumptions, unknowns, conflicts, prerequisites, security implications, economics, operating implications, residual risks, and first milestone.

## P3B-ACT-003 — Gap types — MUST

Distinguish hard prohibition, missing evidence, remediable control gap, strategic tradeoff, and user-owned preference.

## P3B-ACT-004 — Override — MUST

Preserve original recommendation, owner, rationale, accepted risks, timestamp, and required approval.

## P3B-ACT-005 — Portfolio summary — MUST

Group journeys into:

```text
Activate now
Pilot with controls
Use platform-mediated path
Keep human handoff
Do not activate
```

---

# 9. Capability, Platform, and Protocol Inventory

## P3B-CAP-001 — Capability states — MUST

```text
DECLARED
OBSERVED
TESTED
EXECUTABLE_IN_SIMULATION
EXECUTABLE_IN_SANDBOX
UNAVAILABLE
UNKNOWN
```

## P3B-CAP-002 — Anti-gaming — MUST

Declared metadata without executable behavior MUST NOT count as tested readiness.

## P3B-CAP-003 — Platform inventory — MUST

Capture commerce, catalog, inventory, order, customer, payment, fulfillment, and support platforms without implying production support.

## P3B-CAP-004 — Build-versus-mediate guidance — MUST

For missing capabilities, recommend direct exposure, existing platform, intermediary, human handoff, or no activation.

## P3B-PROTO-001 — Exact profiles — MUST

Pin evaluated UCP, ACP, OpenAPI, MCP, and A2A profiles to exact version/source/hash metadata.

## P3B-PROTO-002 — Capability-level results — MUST

Report readiness by supported capability, not a protocol logo or single badge.

## P3B-PROTO-003 — Honest language — MUST

Use `profile mapped`, `fixture validated`, `reference simulation passed`, `gap detected`, or `not evaluated`. Do not claim certification.

## P3B-PROTO-004 — Drift impact — MUST

Map protocol drift to affected journeys, controls, fixtures, recommendations, and blueprint sections.

---

# 10. Controlled Retail Simulation

## P3B-SIM-001 — Scenario runner — MUST

Expose one flow:

```text
discover → select variant → inventory → quote
→ payment authorization simulation → confirmation
→ order → status → cancel/fulfill → return/refund
→ receipts and trace
```

## P3B-SIM-002 — Presets — MUST

Provide happy path, stale inventory, changed price, expired quote, unknown agent, expired delegation, lost response, duplicate retry, cancellation race, payment unknown, duplicate refund, refund over ceiling, connector outage, and human-handoff scenarios.

## P3B-SIM-003 — Reproducibility — MUST

Record scenario version, seed, fake clock, pack/profile versions, connector version, canonical inputs, and result hashes.

## P3B-SIM-004 — Boundary label — MUST

Every result states:

```text
SYNTHETIC SIMULATION — NO PRODUCTION TRANSACTION OCCURRED
```

## P3B-SIM-005 — Retained controls — MUST

Preserve durable idempotency, confirmation binding, receipt separation, unknown-outcome reconciliation, environment binding, refund ceilings, and no blind retry.

---

# 11. CLI Product Experience

Add commands equivalent to:

```bash
agentnative retail init <directory>
agentnative retail validate <directory>
agentnative retail assess <directory> --json
agentnative retail assess <directory> --markdown
agentnative retail journeys <directory>
agentnative retail recommend <directory>
agentnative retail simulate <directory> --scenario <name>
agentnative retail blueprint <directory> --output <path>
agentnative retail evidence <directory> --output <path>
```

Errors MUST distinguish invalid project, missing evidence, hard policy denial, unsupported capability, connector failure, reconciliation required, and internal failure.

All commands MUST work from the installed wheel.

---

# 12. Retail Activation Blueprint

## P3B-REP-001 — Required sections — MUST

1. Executive summary.
2. Business context.
3. Current Retail agent readiness.
4. Priority journey portfolio.
5. Activation recommendation by journey.
6. Architecture options.
7. Capability and platform gaps.
8. Identity, authority, transaction, and human-control model.
9. Protocol/profile readiness.
10. Simulation results.
11. Operating model.
12. 30/60/90-day roadmap.
13. Assumptions and unknowns.
14. Residual risks.
15. Evidence index.

## P3B-REP-002 — Alternatives — MUST

Compare direct, mediated, aggregator, and human-handoff paths where viable.

## P3B-REP-003 — Evidence-backed claims — MUST

Every readiness, safety, maturity, or recommendation claim references evidence or is labeled an assumption.

## P3B-REP-004 — Reproducible identity — MUST

Include project hash, pack version/hash, engine version, protocol profiles, evidence snapshot hash, and generation time.

## P3B-REP-005 — Public-safe output — MUST

Markdown and JSON outputs pass secret/sensitive-data redaction tests.

---

# 13. 30/60/90-Day Roadmap

The generator MUST create:

- Days 1–30: evidence closure, journey selection, capability inventory, policy, ownership, controlled fixtures.
- Days 31–60: protocol/platform path, sandbox connector, operational workflow, incident/reconciliation process, acceptance testing.
- Days 61–90: bounded pilot, monitoring, human handoff, kill switch, support ownership, exit decision.

The roadmap MUST adapt to the recommended pattern. A `DO_NOT_ACTIVATE` result produces a remediation or monitoring plan, not a pretend implementation plan.

---

# 14. Reference Businesses

Create four complete examples:

| Example | Defining condition | Expected result |
|---|---|---|
| Direct-ready retailer | Mature APIs, engineering capacity, fresh inventory, clear authority, viable economics | Bounded `DIRECT` pilot |
| Platform retailer | Strong commerce platform, limited internal engineering | `PLATFORM_MEDIATED` |
| Human-handoff retailer | Useful discovery/quote, weak state-changing automation | `HUMAN_HANDOFF` |
| Unsafe/unviable retailer | Stale inventory, missing authority, weak margins, high exceptions | `DO_NOT_ACTIVATE` |

Each includes expected decisions, evidence, missing gates, simulation presets, and blueprint snapshot tests.

---

# 15. Proportional Test Gate

## P3B-TEST-001 — Full regression — MUST

All existing Phase 1, Phase 2, Phase 3, mutation, package, and CLI tests pass.

## P3B-TEST-002 — Durable concurrency — MUST

Test duplicate purchase, final-unit inventory race, duplicate cancellation, duplicate refund, and partial refunds. Expected: no duplicate side effect and no refund above eligible value.

## P3B-TEST-003 — Restart safety — MUST

Restart between downstream success and response for purchase and refund. Expected: replay or reconciliation, never blind duplicate execution.

## P3B-TEST-004 — Blueprint snapshots — MUST

The four examples produce stable semantic blueprint results, excluding timestamps and paths.

## P3B-TEST-005 — Recommendation directionality — MUST

Increasing risk or removing evidence MUST NOT produce a less-controlled recommendation without compensating evidence.

## P3B-TEST-006 — Installed workflow — MUST

From a clean wheel:

```text
init → validate → assess → recommend → simulate → blueprint → evidence
```

must succeed for the reference examples.

## P3B-TEST-007 — Redaction — MUST

Fake secrets in invalid inputs and connector errors MUST NOT appear in reports, receipts, traces, or CLI errors.

## P3B-TEST-008 — No endless pre-product gate — MUST

Broader fuzzing, live HTTP DNS/redirect enforcement, KMS operations, and production connector certification remain future release gates. Document them; do not delay the synthetic product workflow.

---

# 16. Success Metrics

Measure:

- time from initialization to blueprint;
- percentage of claims linked to evidence;
- mandatory control recall;
- unsafe activation recommendations;
- recommendation reproducibility;
- scenario correctness;
- duplicate side-effect count;
- reconciliation accuracy;
- installed-wheel workflow success;
- reviewer comprehension.

Minimum expectations:

```text
0 unsafe activations on mandatory denial cases
0 duplicate purchase/refund side effects in required tests
100% required blueprint sections generated
100% material claims linked to evidence or assumptions
100% primary CLI workflow success on reference examples
```

---

# 17. Required Deliverables

1. Retail project schema.
2. Four reference workspaces.
3. Retail CLI workflow.
4. Journey template library.
5. Capability/platform inventory workflow.
6. Activation decision integration.
7. Scenario runner and presets.
8. Blueprint generator.
9. Evidence-bundle generator.
10. 30/60/90-day roadmap generator.
11. Targeted concurrency and restart tests.
12. Installed-wheel end-to-end test.
13. README Retail quick start.
14. Public-safe sample blueprint.
15. Updated architecture and traceability.
16. `PHASE_3B_PRODUCTIZATION_BUILD_REPORT.md`.
17. Separate Phase 2 status-reconciliation change.

---

# 18. Build Sequence

1. Define workspace schema and four examples.
2. Connect profile, evidence, maturity, journeys, protocols, economics, and recommendation engine.
3. Expose named simulations using existing durable primitives.
4. Generate blueprint, evidence index, and roadmap.
5. Add CLI commands and clean-wheel verification.
6. Run targeted concurrency, restart, directionality, snapshot, and redaction tests.
7. Update documentation and prepare product review.

---

# 19. Exit Gate

The builder may declare:

```text
READY_FOR_PHASE_3B_PRODUCT_REVIEW
```

when:

- the full CLI workflow works from a clean wheel;
- all four examples generate expected recommendation patterns;
- each priority journey shows evidence, assumptions, gaps, and controls;
- simulations demonstrate success, denial, and reconciliation;
- duplicate purchase/refund and restart tests pass;
- blueprint and evidence outputs are complete and reproducible;
- existing regressions and mutations pass;
- limitations distinguish synthetic from production readiness;
- no critical defect can corrupt recommendations, duplicate value-changing actions, expose secrets, or misrepresent evidence.

Phase 3A infrastructure audit status may remain separately tracked. It MUST NOT prevent a Phase 3B synthetic product review unless a critical defect affects the workflow.

---

# 20. Final Demonstration

The completed demonstration should require fewer than ten commands:

```bash
agentnative retail init demo-retailer
agentnative retail validate demo-retailer
agentnative retail assess demo-retailer --json
agentnative retail journeys demo-retailer
agentnative retail recommend demo-retailer
agentnative retail simulate demo-retailer --scenario lost-response
agentnative retail blueprint demo-retailer --output blueprint.md
agentnative retail evidence demo-retailer --output evidence.json
```

The resulting story:

> We modeled a retailer, selected the journeys that matter, chose the safest commercially sensible participation strategy, simulated transaction and failure paths, proved which controls worked, identified what remains missing, and generated an evidence-backed 90-day activation plan.

Security is now the foundation. Phase 3B must build the house.

# v3 BRD Challenge Review

The v3 BRD has the right product thesis: one horizontal control plane with sector packs, explicit participation strategies, multidimensional maturity, and evidence-backed activation blueprints. The following gaps should be added before the sector packs become production claims.

## P0 — clarify before Phase 3B

### 0. Treat external protocol versions as live dependencies

The BRD's shared baseline should not treat protocol versions as timeless constants. As of the v3 review date, UCP publishes dated releases and separates protocol version selection from capability negotiation; ACP documents merchant-owned checkout/payment responsibility; MPP adds machine-payment flows; SMART App Launch 2.2.0 describes both app-launch and backend-service authorization; and the A2A published specification is 0.3.0. Each pack therefore needs an `as_of` date, exact profile/version, source hash or URL, and drift review outcome. A profile that is only “present” is not evidence of interoperability.

### 1. Define the pack ABI, not only the YAML shape

The BRD names fields but does not define the stable runtime contract for:

- pack loader errors and failure modes;
- pack lifecycle (`design`, `preview`, `active`, `deprecated`, `disabled`);
- version compatibility and upgrade/downgrade rules;
- namespace ownership for capability IDs, policy IDs, eval IDs, and evidence IDs;
- whether a pack may add data fields to a core object or only metadata;
- deterministic serialization and hash identity for a pack.

Phase 3A now enforces a minimum versioned manifest, `sector.*` namespace, core compatibility, and reversible registry disablement. The BRD should make those requirements normative.

### 2. Make security properties executable

The current BRD lists controls, but not the security invariants that every pack must prove. Add mandatory invariants for:

- no cross-pack capability or policy resolution;
- no secret/PHI/payment-data leakage in pack reports, traces, eval fixtures, or receipts;
- pack provenance and integrity verification;
- pack dependency pinning and transitive dependency disclosure;
- pack activation authorization and emergency disablement;
- fail-closed behavior when a pack is missing, incompatible, stale, or partially loaded.

### 3. Define the activation recommendation input schema precisely

Inputs such as `technical_capacity`, `api_maturity`, `action_value`, and `human_staff_availability` need controlled vocabularies, unknown handling, provenance, and an `as_of` timestamp. Otherwise recommendation reproducibility is only syntactic: identical strings can conceal different evidence quality.

Add:

```yaml
value:
  value: mature
  source: client_declared | observed | connector_evidence
  observed_at:
  confidence:
```

### 4. Define the production boundary between connector and simulator

The BRD says connectors may execute sandbox actions, but does not specify how the system prevents a sandbox adapter from reaching production. Add an explicit environment binding, endpoint allowlist, credential class, network policy, and negative test for each connector.

## P1 — required for credible sector packs

### 5. Add lifecycle and change management

Sector rules change faster than the core. The BRD should require:

- effective dates and sunset dates for sector rules;
- protocol/profile version pinning with upgrade impact reports;
- migration rules for stored blueprints and receipts;
- rule-change diffing and approval;
- a compatibility matrix across core, pack, connector, and external profile versions.

### 6. Add availability, freshness, and time semantics

Retail inventory, healthcare slots, local-business hours, quotes, grants, and credentials all expire. Add a shared temporal contract for observation time, validity interval, clock source, timezone, stale-after policy, and behavior under clock skew.

### 7. Add commercial unit economics

The BRD describes “commercially meaningful” participation but does not model the economics that determine whether a journey is worth activating. Add:

- agent-originated demand and conversion assumptions;
- protocol/platform fees;
- per-action inference, connector, payment, and human-handoff costs;
- expected support and exception cost;
- margin/commission constraints;
- cost ceilings and abandonment thresholds;
- an explicit “do not activate” outcome when the unit economics do not clear the business threshold.

### 8. Add agent-channel fairness and anti-arbitrage controls

The threat model mentions channel arbitrage, but the product contract needs tests for discriminatory pricing, inventory reservation abuse, rate-limit evasion, policy differences between human/web/agent channels, and intermediary fee leakage. A business should be able to choose channel policy, but not accidentally create an unreviewed privileged lane.

### 9. Add incident and dispute workflows

Receipts prove what the system recorded; they do not resolve “the agent did the wrong thing” disputes. Add journey-level incident states, customer/merchant dispute references, compensation/rollback policy, evidence retention, and escalation ownership.

## P2 — boundary expansion to plan now

### 10. Add multi-agent and intermediary semantics

The current contract treats “agent” as one actor. Real journeys may include a consumer agent, a marketplace agent, a merchant agent, a payment agent, and an internal fulfillment agent. Add actor-chain identity, delegated authority propagation, liability boundaries, and receipt correlation across hops.

### 11. Add accessibility and human-factors acceptance criteria

Human confirmation, denial messages, and handoff are control surfaces. Add comprehension tests for confirmation language, localization, accessibility, timeout behavior, and approval fatigue.

### 12. Add sector exit criteria for readiness claims

The BRD has release gates but no minimum evidence threshold for calling a pack “active.” Require a signed evidence bundle: corpus coverage, mutation results, clean-environment packaging, connector boundary tests, red-team results, and known residual risks.

## Product challenge

The most important boundary decision is this:

> v3 should not be sold as “agent enablement” alone. It should be sold as a sector participation decision system that can recommend *not activating* a journey when risk, economics, evidence, or operating capacity do not justify it.

That means the next build should prioritize decision quality and evidence completeness over the number of protocols or platform logos supported.

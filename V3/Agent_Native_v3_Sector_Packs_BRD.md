# Agent Native v3.0 Product BRD
## Sector Packs and Activation Blueprints for the Agent Economy

**Document status:** AUTHORITATIVE PRODUCT SOURCE OF TRUTH  
**Version:** 3.0 BRD  
**Date:** 2026-09-27  
**Product:** Agent Native  
**Dependency:** Agent Native v2 core  
**Initial sector packs:** Retail, Healthcare Administration, Local Business / SMB  
**Primary audience:** Product engineering, sector SMEs, security, AI/agent architects, enterprise clients, platform partners, QA/evaluation

---

# 0. How to Read This BRD

This document defines Agent Native v3.

v3 MUST NOT fork the Agent Native core into separate products.

Core principle:

> **One horizontal Agent Native control plane. Multiple sector-specific capability, policy, activation, and evaluation packs.**

External standards define their own protocol/regulatory context. This BRD defines product behavior.

A sector pack MUST NEVER claim:

- legal compliance;
- regulatory certification;
- clinical safety certification;
- payment-network certification;
- guaranteed interoperability with every provider.

A sector pack MAY produce:

- technical evidence;
- readiness findings;
- control mappings;
- implementation gaps;
- activation blueprints;
- test results;
- residual-risk statements.

---

# 1. Product Thesis

Agent Native v2 answers:

> **Can this organization safely activate agent access?**

Agent Native v3 answers:

> **What does safe, useful, commercially meaningful agent participation look like for this specific sector and business model, and what is the fastest defensible path to activate it?**

```text
V1  ASSESS
    Can agents understand us?

V2  ACTIVATE + CONTROL
    Can agents interact with us safely?

V3  SECTORIZE + SCALE
    Which agent journeys matter in our sector,
    which controls apply,
    and how should this specific organization participate?
```

---

# 2. Architecture Principle: Sector Packs, Not Sector Forks

Prohibited:

```text
agent-native-retail/
agent-native-healthcare/
agent-native-restaurants/
```

Required model:

```text
Agent Native Core
      │
      ├── Retail Pack
      ├── Healthcare Administration Pack
      └── Local Business Pack
```

Every sector pack MUST use the same:

- capability graph;
- agent identity model;
- delegation model;
- participation policy engine;
- simulator;
- receipt engine;
- evidence model;
- observability model;
- evaluation framework.

Sector-specific business semantics MUST remain in the pack layer.

---

# 3. v3 Product Outcomes

A client using v3 MUST be able to answer:

1. Which agent-native customer/operational journeys matter in our sector?
2. Which capabilities should we expose?
3. Which agent channels should we allow?
4. Which existing platforms can mediate our participation?
5. Where do we need direct protocols/APIs?
6. Which actions require agent identity, user authority, payment, consent, or confirmation?
7. What sector-specific failure modes matter?
8. What does good look like for our risk/business model?
9. What should we build first?
10. How do we test it before broad exposure?
11. How do we monitor it continuously?
12. What evidence can executives, security, product, and engineering inspect together?

---

# 4. Initial Sector Strategy

v3 MUST launch with three intentionally different packs.

## 4.1 Retail

Primary architecture stressor:

> **transaction complexity**

Retail forces the core to handle discovery, price, inventory, checkout, payment, fulfillment, cancellation, refunds, trust, and race conditions.

## 4.2 Healthcare Administration

Primary architecture stressor:

> **identity, privacy, consent, data sensitivity, and consequence**

Initial scope is administrative and patient-service workflows.

The pack MUST NOT support autonomous:

- diagnosis;
- treatment selection;
- prescribing;
- medication dosing;
- autonomous clinical triage;
- autonomous modification of clinical records;
- clinical decision-making.

## 4.3 Local Business / SMB

Primary architecture stressor:

> **activation simplicity and distribution**

Question:

> Can a nontechnical business participate in the agent economy without becoming an API company?

The pack MUST prioritize existing platforms and human handoff over unnecessary custom infrastructure.

---

# 5. Sector Pack Contract

Every pack MUST implement this declarative contract:

```yaml
pack_id:
pack_version:
sector:
subsectors:
core_version_requirement:

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
```

---

# 6. Generic Sector Pack Requirements

## V3-PACK-001 — Declarative manifest — MUST

A pack MUST declare supported sector/subsectors, pack version, compatible core version, capability profiles, evals, and reference architectures.

## V3-PACK-002 — No core monkey-patching — MUST

A pack MUST NOT modify core behavior through monkey-patching, undocumented import hooks, or hidden global state.

## V3-PACK-003 — Capability extension — MUST

Sector capabilities MUST extend the canonical v2 capability object.

## V3-PACK-004 — Control extension — MUST

Sector controls MUST map to v2 policy constructs rather than inventing a parallel policy engine.

## V3-PACK-005 — Eval isolation — MUST

A failing healthcare pack eval MUST NOT invalidate retail execution.

## V3-PACK-006 — External-version pinning — MUST

Every pack MUST declare the external protocol/profile versions it evaluates.

## V3-PACK-007 — Evidence traceability — MUST

Every finding MUST map:

```text
sector requirement
→ capability/control
→ evidence
→ evaluation
→ recommendation
```

## V3-PACK-008 — Pack dependency transparency — MUST

A sector pack MUST list required and optional adapters/connectors.

## V3-PACK-009 — Safe uninstall/disable — MUST

Disabling a pack MUST NOT alter core behavior or corrupt stored results.

---

# 7. Agent Participation Strategy

v3 MUST introduce a formal client participation strategy. Businesses MUST NOT be told that direct exposure to every agent is the default target state.

Agent Native MUST support these activation patterns.

## 7.1 DIRECT

The business exposes its own agent-facing interfaces.

Appropriate when:

- APIs are mature;
- direct control is strategically valuable;
- engineering/security capacity exists;
- economics justify direct participation.

## 7.2 PLATFORM_MEDIATED

The business participates through an existing commerce, booking, POS, payments, scheduling, marketplace, or industry platform.

Appropriate when:

- the platform already owns the workflow;
- direct integration duplicates existing capability;
- engineering capacity is limited;
- the platform provides acceptable control/evidence.

## 7.3 AGGREGATOR_MARKETPLACE

The business participates through a marketplace/industry aggregator.

Appropriate when discovery and transaction orchestration already occur through that intermediary.

## 7.4 HUMAN_HANDOFF

Agents may discover, gather context, create a lead, or begin a workflow while a human completes the consequential action.

Appropriate when:

- consequence is high;
- API maturity is low;
- policy requires review;
- integration cost exceeds likely benefit.

---

# 8. Activation Strategy Engine

## V3-ACT-001 — Required inputs — MUST

```yaml
business_size:
technical_capacity:
api_maturity:
existing_platforms:
transaction_volume:
action_value:
data_sensitivity:
regulatory_sensitivity:
reversibility:
customer_identity_requirement:
payment_requirement:
real_time_inventory_requirement:
human_staff_availability:
agent_channel_priority:
expected_agent_volume:
```

## V3-ACT-002 — Required output — MUST

Output:

- recommended activation pattern;
- viable alternatives;
- rationale/evidence;
- prerequisites;
- integration complexity band;
- security implications;
- operating-model implications;
- first implementation milestone.

## V3-ACT-003 — No opaque recommendation score — MUST

Do not emit one unexplained numeric score.

## V3-ACT-004 — Explicit tradeoffs — MUST

Example:

```text
PLATFORM_MEDIATED

Gains
- faster activation
- lower engineering burden
- existing platform primitives

Tradeoffs
- less direct control
- platform dependency
- channel-specific constraints
```

## V3-ACT-005 — Human override — MUST

Client decision-makers MUST be able to select a different strategy, and the override MUST be recorded.

## V3-ACT-006 — Recommendation assumptions — MUST

Every recommendation MUST identify assumptions that materially affect it.

---

# 9. Sector Maturity Model

v3 MUST use a multi-dimensional maturity model. There MUST NOT be a single composite Agent Native score.

## 9.1 Levels

```text
L0 — Invisible
No reliable machine-facing participation.

L1 — Discoverable
Agents can identify the business and basic offerings.

L2 — Understandable
Capabilities, constraints, terms, and schemas are machine-readable.

L3 — Callable
Agents can invoke bounded low-risk capabilities.

L4 — Transactable
Agents can safely perform controlled state-changing workflows.

L5 — Orchestratable
Long-running, cross-system, policy-controlled agent workflows
operate with traceability and recovery.
```

## 9.2 Required maturity dimensions

Each sector MUST assess separately:

1. discovery;
2. capability semantics;
3. agent identity;
4. delegated authority;
5. transaction/action safety;
6. data access;
7. recovery;
8. observability;
9. human control;
10. ecosystem interoperability;
11. sector-specific controls;
12. operating-model readiness.

## V3-MAT-001 — Evidence-gated maturity — MUST
A level is assigned only when all mandatory criteria for that level are satisfied.

## V3-MAT-002 — No averaging — MUST
L5 discovery MUST NOT compensate for L1 authorization.

## V3-MAT-003 — Maturity evidence — MUST
Every level assignment MUST list evidence and missing gates.

---

# 10. Client Deliverables

## V3-REP-001 — Sector Agent Economy Blueprint — MUST

Sections:

1. business context;
2. current agent readiness;
3. sector capability map;
4. priority agent journeys;
5. activation strategy;
6. target architecture;
7. agent participation matrix;
8. control requirements;
9. protocol/platform approach;
10. human-control model;
11. evaluation plan;
12. implementation roadmap;
13. residual risks.

## V3-REP-002 — Journey Portfolio — MUST

```yaml
journey_id:
persona:
agent_goal:
business_goal:
capabilities:
data_needed:
agent_trust_required:
principal_required:
payment_required:
risk_level:
confirmation:
reversibility:
human_handoff:
protocols:
platform_dependencies:
eval_scenarios:
```

## V3-REP-003 — 90-Day Activation Plan — MUST

Must identify:

- first production-safe journey;
- first protocol/platform integration;
- first policy set;
- first simulator scenario;
- first operational dashboard;
- owners/dependencies;
- exit criteria.

## V3-REP-004 — Architecture Options — MUST

The report MUST compare at least direct vs mediated vs human-handoff when more than one is viable.

---

# 11. Retail Sector Pack

**Pack ID:** `sector.retail`

Initial retail scope SHOULD cover general merchandise, apparel, direct-to-consumer, consumer ecommerce, and omnichannel catalog/fulfillment.

Regulated product categories require later specialized sub-packs.

---

# 12. Retail Capability Taxonomy

The retail pack MUST model at least:

```text
DISCOVERY
- search_catalog
- get_product
- get_variant
- compare_products
- get_availability

COMMERCIAL CONTEXT
- get_price
- get_promotion
- get_tax_estimate
- get_shipping_options
- get_delivery_estimate

CART / CHECKOUT
- create_cart
- update_cart
- create_checkout
- update_checkout
- preview_order
- submit_order

POST PURCHASE
- get_order_status
- change_order
- cancel_order
- initiate_return
- get_return_status
- request_refund

CUSTOMER
- identify_customer
- apply_loyalty
- retrieve_entitlements
```

Each capability MUST declare sector risk semantics.

---

# 13. Retail Protocol Profiles

The retail pack SHOULD support readiness/conformance profiles for:

- Universal Commerce Protocol (UCP);
- OpenAI Agentic Commerce Protocol (ACP);
- OpenAPI commerce APIs;
- MCP commerce tools where exposed;
- A2A commerce agents where exposed.

Payment/trust profiles MAY include:

- Machine Payments Protocol (MPP);
- Visa Trusted Agent Protocol;
- future payment-scheme agent identity mechanisms through extensions.

Protocol presence alone MUST NOT produce a transaction-safety PASS.

---

# 14. Retail Functional Requirements

## V3-RET-001 — Stable catalog identity — MUST
Products and variants MUST have stable machine identifiers.

## V3-RET-002 — Variant disambiguation — MUST
Ambiguous size/color/configuration selection MUST be detectable.

## V3-RET-003 — Inventory freshness — MUST
Inventory evidence MUST include observation/freshness context where available.

## V3-RET-004 — Price provenance — MUST
Transaction evidence MUST preserve quoted price, currency, tax status, shipping, discount, and quote timestamp.

## V3-RET-005 — Quote expiration — SHOULD
A quote SHOULD expose expiry or refresh semantics.

## V3-RET-006 — Price-change handling — MUST
If price materially changes between preview and commit, the transaction MUST NOT silently proceed when merchant policy requires reconfirmation.

## V3-RET-007 — Inventory race — MUST
Simulation MUST test inventory loss between discovery and order submission.

## V3-RET-008 — Idempotent checkout — MUST
Duplicate checkout/order submissions MUST be tested.

## V3-RET-009 — Agent identity classes — MUST
Retail policy MUST distinguish unknown automation, recognized agent, verified commerce agent, partner, and internal agent.

## V3-RET-010 — Customer delegation — MUST
Customer-specific price, loyalty, saved addresses, and account data require appropriate customer authority.

## V3-RET-011 — Payment separation — MUST
Agent Native MUST NOT become the payment processor.

## V3-RET-012 — Confirmation thresholds — MUST
Merchants MUST be able to configure value/risk thresholds requiring confirmation.

Example only:

```text
< $50       autonomous if explicitly delegated
$50-$500    user confirmation
> $500      user confirmation + stronger auth
```

Actual thresholds are merchant-owned.

## V3-RET-013 — Refund separation — MUST
Refund permission MUST be independently authorized from purchase permission.

## V3-RET-014 — Return eligibility — MUST
If return eligibility cannot be machine-evaluated, the limitation/human handoff MUST be explicit.

## V3-RET-015 — Merchant risk override — MUST
Merchant fraud/risk policy MAY deny an action. Result MUST be machine-readable without exposing internal fraud logic.

## V3-RET-016 — Order receipt — MUST
A successful order MUST produce a receipt/order reference that can be correlated with Agent Native's receipt.

## V3-RET-017 — Fulfillment state — MUST
Agents MUST distinguish order accepted, processing, fulfilled, partially fulfilled, cancelled, and failed where supported.

---

# 15. Retail Required Eval Scenarios

At minimum:

1. stale inventory;
2. price increase after quote;
3. price decrease after quote;
4. duplicate order retry;
5. payment authorization timeout;
6. order succeeded but response lost;
7. coupon stacking attempt;
8. loyalty mismatch;
9. shipping option invalidation;
10. address changed after confirmation;
11. wrong variant;
12. return outside policy;
13. duplicate refund request;
14. unknown agent purchase attempt;
15. verified agent with expired user grant;
16. fake verified-commerce identity;
17. checkout says success but merchant order absent;
18. partial fulfillment;
19. cancellation racing fulfillment;
20. conflicting UCP/ACP metadata.

---

# 16. Retail Reference Sources

- Universal Commerce Protocol — Shopify  
  https://www.shopify.com/ucp

- UCP technical overview — Google  
  https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp/

- Agentic Commerce Protocol — OpenAI  
  https://developers.openai.com/commerce

- Machine Payments Protocol — Stripe  
  https://stripe.com/blog/machine-payments-protocol

- Trusted Agent Protocol — Visa  
  https://developer.visa.com/capabilities/trusted-agent-protocol/trusted-agent-protocol-specifications

Retail adapters MUST pin protocol/profile versions wherever external versioning exists.

---

# 17. Healthcare Administration Sector Pack

**Pack ID:** `sector.healthcare_admin`

The name deliberately includes `_admin`.

The initial release focuses on administrative and patient-service workflows, not autonomous clinical decision-making.

---

# 18. Healthcare Administrative Capability Taxonomy

```text
PUBLIC DISCOVERY
- find_provider
- get_location
- get_service
- get_hours
- get_public_appointment_availability

PATIENT AUTHENTICATED
- schedule_appointment
- reschedule_appointment
- cancel_appointment
- retrieve_appointment
- retrieve_billing_summary
- retrieve_coverage_information
- submit_administrative_document
- retrieve_patient_requested_document
- request_human_support

CONTROLLED REQUESTS
- request_medication_refill
- request_record_transfer
- request_prior_authorization_status
```

A request capability is not equivalent to approving a clinical action.

---

# 19. Healthcare Trust Zones

The pack MUST model:

```text
H0 — PUBLIC
No patient identity required.

H1 — PATIENT-BOUND ADMIN
Patient identity required; limited administrative data.

H2 — PROTECTED HEALTH DATA
Explicit patient/authorized-user access and data minimization required.

H3 — CLINICAL WORKFLOW BOUNDARY
Clinician/system-of-record controls dominate.

H4 — AUTONOMOUS CLINICAL ACTION
OUT OF SCOPE for initial v3 healthcare pack.
```

---

# 20. Healthcare Requirements

## V3-HC-001 — Identity before PHI — MUST
Protected health information MUST NOT be returned merely because an agent identifies itself. Patient/authorized-principal authority is separate.

## V3-HC-002 — Minimum necessary — MUST
The pack MUST evaluate whether requested data is broader than needed for the declared administrative purpose.

## V3-HC-003 — Purpose binding — MUST
A protected-data delegation MUST identify a purpose/category.

## V3-HC-004 — FHIR capability discovery — MUST
Where FHIR exists, inspect relevant capability metadata and supported resource interactions.

## V3-HC-005 — SMART configuration — MUST
Where SMART App Launch exists, inspect `.well-known/smart-configuration` and advertised authorization capabilities.

## V3-HC-006 — SMART scope analysis — MUST
Compare requested scopes to the administrative capability. Broad clinical scope for narrow scheduling MUST trigger a privilege warning/failure according to profile.

## V3-HC-007 — Patient-context binding — MUST
Patient-bound actions MUST validate patient context binding where supported.

## V3-HC-008 — Separate appointment actions — MUST
Schedule, reschedule, and cancel MUST be separately represented and authorized.

## V3-HC-009 — Clinical boundary — MUST
The pack MUST identify and stop at actions requiring clinical decision authority.

## V3-HC-010 — Refill request distinction — MUST
A refill **request** MAY be modeled. Autonomous medication approval/prescribing MUST NOT be modeled as an allowed administrative capability.

## V3-HC-011 — Clinical record mutation restriction — MUST
The reference simulator MUST NOT autonomously modify clinical records.

## V3-HC-012 — PHI audit event — MUST
Protected administrative actions MUST emit an audit event containing identity reference, principal reference, purpose, scope, resource class, action, result, timestamp, and trace reference.

## V3-HC-013 — Data minimization in evidence — MUST
Public reports MUST NOT retain raw PHI merely to prove a finding. Synthetic data is REQUIRED for public examples.

## V3-HC-014 — Human escalation — SHOULD
Administrative workflows SHOULD expose human escalation when safe continuation is impossible.

## V3-HC-015 — Revocation — MUST
Revoked authority MUST stop subsequent protected access.

## V3-HC-016 — Access control evidence — MUST
The pack MUST distinguish agent identity, user/patient identity, and resource authorization.

## V3-HC-017 — Transmission/security boundary — MUST
Protected-data simulations MUST require secure transport and MUST fail closed on invalid trust configuration.

---

# 21. Healthcare Required Eval Scenarios

At minimum:

1. public provider search without patient identity;
2. appointment scheduling with valid delegation;
3. wrong-patient context;
4. expired patient grant;
5. excessive SMART scopes;
6. revoked access;
7. unrelated PHI request beyond task need;
8. scheduling endpoint returns clinical note accidentally;
9. duplicate appointment creation;
10. cancellation retry;
11. refill request treated incorrectly as medication authorization;
12. autonomous clinical record update attempt;
13. cross-patient token confusion;
14. audit event missing purpose;
15. PHI leaks into Agent Native output;
16. patient identity valid but agent identity unknown;
17. agent identity valid but patient authority missing;
18. SMART discovery mismatch;
19. FHIR capability mismatch;
20. required human escalation.

---

# 22. Healthcare Reference Sources

- HL7 SMART App Launch 2.2.0  
  https://www.hl7.org/fhir/smart-app-launch/

- SMART scopes and launch context  
  https://hl7.org/fhir/smart-app-launch/STU2.2/scopes-and-launch-context.html

- HHS HIPAA Security Rule summary  
  https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html

- HHS Minimum Necessary guidance  
  https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/minimum-necessary-requirement/index.html

- CMS Interoperability Framework  
  https://www.cms.gov/initiatives/health-technology-ecosystem/overview/interoperability-framework

Agent Native MUST NOT represent a technical finding as HIPAA compliance certification.

---

# 23. Local Business / SMB Sector Pack

**Pack ID:** `sector.local_business`

Representative businesses:

- restaurants;
- salons;
- plumbers;
- electricians;
- cleaners;
- fitness studios;
- tutors;
- repair shops;
- photographers;
- local professional services;
- independent retailers.

Goal:

> **Make a business usable by agents without forcing the owner to become an API architect.**

---

# 24. Local Business Capability Taxonomy

```text
DISCOVERY
- get_business_identity
- get_location
- get_hours
- get_service_area
- get_services
- get_price_guidance

LEAD / QUOTE
- request_quote
- submit_job_context
- request_callback

SCHEDULING
- get_availability
- reserve_slot
- schedule
- reschedule
- cancel

COMMERCE
- create_order
- pay_deposit
- pay_invoice

SUPPORT
- get_status
- ask_question
- request_human
```

Not every business must implement every capability.

---

# 25. Platform-First Principle

## V3-LB-001 — Existing platform inventory — MUST

Before recommending custom interfaces, Agent Native MUST identify relevant existing system categories:

- website/CMS;
- ecommerce;
- POS;
- payments;
- scheduling/calendar;
- CRM;
- booking;
- ordering/delivery;
- communications.

## V3-LB-002 — Avoid unnecessary custom infrastructure — MUST

If an existing platform can expose the required capability with acceptable controls, the activation engine SHOULD prefer platform-mediated participation.

## V3-LB-003 — Explain custom-build gaps — MUST

If custom work is recommended, identify the exact missing capability/control not provided by the existing platform.

---

# 26. Local Business Onboarding Experience

The target user may have no API knowledge.

The onboarding flow MUST be understandable in business language:

```text
1. Enter business website
2. Confirm business ownership
3. Detect/declare existing platforms
4. Confirm services, hours, location, service area
5. Select what agents may do
6. Connect supported platforms
7. Define approval/value limits
8. Run synthetic customer scenarios
9. Review failures and human handoffs
10. Activate selected capability
```

---

# 27. Local Business Requirements

## V3-LB-004 — Plain-language controls — MUST

Example:

```text
AI agents may:
[x] answer business questions
[x] show available times
[x] request a quote
[x] book an appointment under $200
[ ] charge more than $200
[ ] issue refunds
```

The product MAY compile this into formal v2 policy.

## V3-LB-005 — Human handoff — MUST
Every local-business configuration MUST support a human-handoff strategy.

## V3-LB-006 — Service area — MUST
Service-area constraints MUST be machine-readable when material.

## V3-LB-007 — Hours/exceptions — SHOULD
Business hours, holidays, and exceptional closures SHOULD be representable.

## V3-LB-008 — Price semantics — MUST

```text
FIXED_PRICE
STARTING_AT
ESTIMATE
QUOTE_REQUIRED
```

An estimate MUST NOT be represented as a guaranteed price.

## V3-LB-009 — Deposit vs charge — MUST
Where applicable, distinguish deposit, payment authorization, invoice, and final charge.

## V3-LB-010 — Booking idempotency — MUST
Duplicate booking retries MUST be tested.

## V3-LB-011 — Capacity race — MUST
Simulation MUST test two requests competing for the same slot/resource.

## V3-LB-012 — Owner control — MUST
Owners MUST be able to disable an agent capability without redeploying source code.

## V3-LB-013 — Emergency stop — MUST
State-changing agent actions MUST have a rapid kill switch.

## V3-LB-014 — Human-led can be successful — MUST
A business MAY be successfully activated at lower autonomy when human handoff is intentional.

## V3-LB-015 — Platform outage — MUST
The product MUST define fallback/handoff behavior when a connected platform is unavailable.

## V3-LB-016 — Credential expiry — MUST
Expired connector credentials MUST fail safely and produce actionable owner guidance.

---

# 28. Local Business Required Eval Scenarios

At minimum:

1. unexpected closure;
2. slot race;
3. quote-required service but agent tries purchase;
4. agent turns "starting at" into fixed price;
5. duplicate booking;
6. deposit charged twice;
7. outside service area;
8. unknown agent attempts refund;
9. customer changes appointment after confirmation;
10. platform unavailable;
11. owner disables capability mid-session;
12. human handoff unavailable;
13. stale business hours;
14. prompt-injection content on website;
15. unsupported service requested;
16. booking succeeds but response is lost;
17. cancellation after cutoff;
18. platform credentials expired;
19. website-only business with no API;
20. platform-mediated path exists and custom build is unnecessary.

---

# 29. Sector Policy Profiles

Each sector pack MUST provide starter templates:

```text
CONSERVATIVE
BALANCED
AUTOMATION_FORWARD
```

These are templates, not recommendations or rankings.

Each template MUST expose exactly what changes.

Example:

```text
Retail purchase confirmation

CONSERVATIVE
  Always require confirmation.

BALANCED
  Autonomous below explicit merchant threshold.

AUTOMATION_FORWARD
  Autonomous within delegated budget and merchant policy.
```

Users MUST explicitly select/customize a profile.

---

# 30. Sector Control Mapping

Each pack MUST maintain:

```text
sector requirement
→ Agent Native control
→ evidence type
→ evaluation
→ external reference (if applicable)
```

External mappings MUST be labeled as supporting evidence, never as certification.

---

# 31. Sector Evaluation Harness

## V3-EVAL-001 — Pack-specific corpus — MUST
Every pack MUST include positive, partial-maturity, deceptive, malformed, and high-risk references.

## V3-EVAL-002 — Core regression — MUST
Installing a pack MUST NOT regress Agent Native core tests.

## V3-EVAL-003 — Cross-pack isolation — MUST
Retail semantics MUST NOT affect healthcare results.

## V3-EVAL-004 — Journey test minimum — MUST
Every priority journey requires happy path, denied path, expired authority, duplicate/retry, partial failure, and human handoff where applicable.

## V3-EVAL-005 — Anti-gaming — MUST
Test ideal-looking metadata with broken/nonexistent executable capability.

## V3-EVAL-006 — Human factors — SHOULD
Configuration UX SHOULD be tested for whether non-specialists understand what agents can/cannot do and when humans are required.

## V3-EVAL-007 — Recommendation reproducibility — MUST
Identical inputs and pack versions MUST yield semantically equivalent activation recommendations.

---

# 32. Cross-Sector Threat Model Additions

v3 MUST add threat coverage for:

- agent-channel arbitrage;
- malicious marketplace/aggregator;
- cross-sector capability confusion;
- hidden platform privilege;
- business-rule manipulation;
- stale price/availability;
- identity laundering through intermediary;
- excessive personal-data retrieval;
- overbroad delegation;
- unsafe automation thresholds;
- human-approval fatigue;
- platform outage;
- connector credential compromise;
- duplicate transactions;
- incorrect compensation;
- sector-pack supply-chain compromise.

Each pack MUST publish a threat delta on top of the v2 threat model.

---

# 33. Connector Architecture

v3 SHOULD distinguish protocol adapters from business-system connectors.

```text
Protocol Adapter
Understands a standard/protocol.

Connector
Integrates with a specific platform/system.
```

A connector SHOULD implement, where applicable:

```text
discover_capabilities
map_to_capability_graph
test_connection
read_configuration
execute_sandbox_action
normalize_result
emit_trace
```

Credentials MUST remain in a dedicated secret boundary and MUST NOT be embedded in pack files.

---

# 34. Connector Priority

v3 SHOULD favor a few deeply tested connectors over a logo wall.

## Retail
1. generic OpenAPI commerce reference;
2. Shopify-oriented reference integration;
3. payment-protocol reference adapter.

## Healthcare
1. synthetic FHIR server;
2. SMART App Launch reference integration.

## Local Business
1. generic scheduling connector interface;
2. generic payment connector interface;
3. one reference SMB platform integration.

The exact commercial platform MAY vary based on stable sandbox access and contributor support.

---

# 35. Client Workshop Mode

v3 SHOULD support a structured workshop workflow.

## Stage 1 — Participate or Block?
Define strategic stance toward agent channels.

## Stage 2 — Priority Journeys
Select 3–5 journeys based on client-defined business/customer priorities.

## Stage 3 — Capability Decomposition
Break journeys into machine capabilities.

## Stage 4 — Control Boundaries
Define identity, authority, data, value, confirmation, human handoff, and recovery.

## Stage 5 — Activation Pattern
Choose direct, platform-mediated, aggregator, or human handoff.

## Stage 6 — Simulation
Test controlled scenarios.

## Stage 7 — Roadmap
Produce 30/60/90-day implementation sequence.

The product MUST generate reusable artifacts from these stages.

---

# 36. Client Prioritization Dimensions

Agent Native MAY show dimensions but MUST NOT collapse them into an opaque winner/score.

Required dimensions:

- business value;
- customer value;
- technical feasibility;
- data sensitivity;
- transaction risk;
- reversibility;
- platform leverage;
- integration complexity band;
- operating-model complexity.

The client owns the prioritization decision.

---

# 37. v3 Build Phases

## Phase 3A — Sector Pack SDK

Build:

- manifest/loader;
- capability extensions;
- maturity framework;
- activation strategy engine;
- sector report extensions;
- pack eval harness.

**Exit gate:** a synthetic pack extends Agent Native without modifying core code.

## Phase 3B — Retail Pack

Build:

- retail taxonomy;
- UCP/ACP profiles;
- commerce transaction scenarios;
- agent trust/payment identity profiles;
- retail activation blueprint;
- reference retail environment.

**Exit gate:** Agent Native can assess and simulate catalog → quote → checkout → order → cancellation with policy and recovery evidence.

## Phase 3C — Local Business Pack

Build:

- simple onboarding;
- platform inventory;
- activation strategy;
- scheduling/quote/payment templates;
- human-handoff workflows;
- reference integration.

**Exit gate:** a nontechnical reference business can select allowed agent actions, simulate booking, and produce an activation blueprint without writing protocol code.

## Phase 3D — Healthcare Administration Pack

Build:

- FHIR/SMART profiles;
- patient/principal binding;
- PHI-aware evidence controls;
- appointment/admin workflows;
- clinical-boundary controls;
- healthcare eval corpus.

**Exit gate:** Agent Native can test public discovery and controlled patient-authorized admin workflows while blocking out-of-scope clinical autonomy.

---

# 38. v3 Release Gates

## Core / Pack Architecture

- packs load without modifying core;
- compatibility is enforced;
- cross-pack isolation passes.

## Retail

- mandatory scenarios pass;
- duplicate purchase protection demonstrated;
- price/inventory race visible;
- unknown-agent purchase policy enforceable;
- receipts remain complete.

## Healthcare

- synthetic PHI cannot leak into public reports;
- wrong-patient context is rejected;
- expired/revoked authority is rejected;
- autonomous clinical actions are blocked by scope;
- minimum-necessary analysis works on reference cases.

## Local Business

- platform-mediated strategy can be selected;
- human handoff works;
- owner kill switch works;
- booking duplicate/race scenarios are handled;
- price semantics distinguish estimate vs fixed price.

## Evidence

- every sector finding has evidence;
- every recommendation states assumptions;
- every maturity assignment identifies gate criteria.

---

# 39. v3 Non-Goals

v3 MUST NOT:

- become an EHR;
- become a medical agent;
- diagnose or prescribe;
- become a payment network;
- unnecessarily hold card data;
- become an ecommerce platform;
- become a POS;
- build custom software for every small business;
- guarantee legal compliance;
- optimize clients for a single agent provider;
- make strategic choices for clients through opaque scoring.

---

# 40. Success Metrics

## Platform metrics

- protocol/connector coverage measured by tested capability, not logo count;
- percentage of sector requirements with executable evals;
- false-positive/false-negative rate on controlled corpus;
- time to produce sector activation blueprint;
- percentage of recommendations with explicit evidence;
- number of cross-protocol journeys successfully simulated.

## Client-value metrics

Pilots SHOULD measure:

- time from assessment to first safe agent journey;
- engineering effort avoided through platform mediation;
- percentage of agent actions with complete trace/receipt;
- human-handoff rate;
- duplicate/retry incident rate;
- policy-denied unsafe action rate;
- time to deactivate a risky capability.

These MUST NOT be represented as proof of financial ROI without client data.

---

# 41. Product Packaging

```text
Agent Native Core
  ├── Assess
  ├── Protocols
  ├── Identity
  ├── Policy
  ├── Simulator
  ├── Receipts
  └── Edge

Agent Native Packs
  ├── Retail
  ├── Healthcare Administration
  └── Local Business

Agent Native Outputs
  ├── Readiness Profile
  ├── Agent Participation Blueprint
  ├── Sector Activation Blueprint
  ├── Capability Exposure Matrix
  ├── Simulation Evidence
  └── 90-Day Activation Plan
```

---

# 42. Long-Term Expansion Candidates

Only after the first three packs prove the abstraction:

- travel;
- financial services;
- insurance;
- professional services;
- logistics;
- public sector;
- education.

A new sector SHOULD be added only when it introduces materially new architecture/control requirements or demonstrated user demand.

---

# 43. Key Product Decisions

1. Sector intelligence lives in packs, not forks.
2. Participation can be direct, mediated, aggregated, or human-led.
3. Maximum autonomy is not the definition of success.
4. Maturity is multidimensional; no overall score.
5. Retail is the first transaction-stress pack.
6. Healthcare starts with administrative workflows, not autonomous clinical decisions.
7. Local business prioritizes activation simplicity over protocol sophistication.
8. Existing platforms are assets, not obstacles.
9. Every sector recommendation exposes tradeoffs.
10. Every sector pack requires adversarial tests before release.

---

# 44. External Reference Baseline

## Retail / Commerce

- Universal Commerce Protocol — Shopify  
  https://www.shopify.com/ucp

- Universal Commerce Protocol technical overview — Google  
  https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp/

- Agentic Commerce Protocol — OpenAI  
  https://developers.openai.com/commerce

- Machine Payments Protocol — Stripe  
  https://stripe.com/blog/machine-payments-protocol

- Trusted Agent Protocol — Visa  
  https://developer.visa.com/capabilities/trusted-agent-protocol/trusted-agent-protocol-specifications

## Healthcare

- SMART App Launch 2.2.0 — HL7  
  https://www.hl7.org/fhir/smart-app-launch/

- SMART scopes and launch context  
  https://hl7.org/fhir/smart-app-launch/STU2.2/scopes-and-launch-context.html

- HIPAA Security Rule summary — HHS  
  https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html

- HIPAA Minimum Necessary guidance — HHS  
  https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/minimum-necessary-requirement/index.html

- CMS Interoperability Framework  
  https://www.cms.gov/initiatives/health-technology-ecosystem/overview/interoperability-framework

## Shared Infrastructure

- Agent Native v2 BRD
- Agent Native v1 repository baseline
- MCP 2026-07-28
- A2A 1.0.0
- OAuth Security BCP / DPoP / HTTP Message Signatures

---

# 45. Final Product Statement

Agent Native v3 is complete when a client can credibly say:

> **We understand how agents should participate in our sector, which journeys matter, what capabilities and controls they require, whether we should integrate directly or through existing platforms, how to test those journeys safely, and exactly what we need to build over the next 90 days.**

v1 proves readiness.

v2 proves controlled interoperability.

v3 turns that foundation into a **repeatable sector activation system for the agent economy**.

# Agent Native v0.1 — Master Build Prompt for Codex

## Role

You are the **Principal Engineer, Product Architect, Security Engineer, Evaluation Lead, and Developer Experience owner** responsible for building the first public version of **Agent Native**.

You have been given the attached:

`Agent_Native_Product_BRD_v1.0`

**Read the entire BRD before writing code.**

The BRD is the authoritative product source of truth.

Do not casually reinterpret requirements.  
Do not expand scope because an adjacent feature seems interesting.  
Do not invent a new protocol when an existing standard is sufficient.  
Do not optimize for demo theatrics over engineering quality.

Where this implementation prompt and the BRD differ:

1. Explicit requirements in the BRD win.
2. Security constraints choose the safer interpretation.
3. If ambiguity remains, document the assumption in an ADR.
4. Do not silently make material product decisions.

---

# 1. Mission

Build **Agent Native v0.1**:

> An open-source toolkit that determines whether a digital business is discoverable, understandable, interoperable, and safely usable by AI agents.

The central product question is:

> **Can an AI agent actually do business with you?**

Version 0.1 is **not**:

- a generic AI agent;
- an autonomous penetration-testing platform;
- a compliance certification tool;
- an MCP wrapper generator;
- an arbitrary web crawler;
- a single-number “Agent Native Score.”

Version 0.1 is:

```text
TARGET
  ↓
Safe Acquisition
  ↓
Artifact Discovery
  ↓
Normalization
  ↓
Deterministic Checks
  ↓
Evidence
  ↓
Findings
  ↓
Actionable Report
```

The initial goal is to prove that Agent Native can produce **trustworthy, repeatable, explainable evidence**.

---

# 2. Product Principles

Follow these principles throughout the implementation.

1. Evidence before opinion.
2. Deterministic checks before LLM judgment.
3. Safety before scan coverage.
4. Explain findings rather than merely classifying them.
5. Preserve raw evidence necessary to reproduce a result.
6. Never claim regulatory certification.
7. Never equate lack of observable evidence with definite absence.
8. Treat every scanned target as untrusted input.
9. Treat every fetched artifact as potentially malicious.
10. Never execute content obtained from a scanned target.
11. Minimize network privileges.
12. Explicitly separate passive inspection from active interaction.
13. Protocol adapters must remain modular.
14. Do not create unnecessary standards.
15. Build interfaces that can later support:
   - MCP
   - A2A
   - OpenAPI
   - additional agent ecosystems
16. Keep evaluation logic independent from presentation.
17. Make every important behavior testable.
18. Prefer inspectable engineering over hidden LLM behavior.
19. Failed checks must say **why** they failed.
20. `UNKNOWN`, `NOT_OBSERVED`, and `FAIL` must remain distinguishable.

---

# 3. Version 0.1 Scope

## 3.1 CLI

Primary invocation:

```bash
agentnative scan https://example.com
```

Useful commands should include:

```bash
agentnative scan <target>
agentnative scan <target> --json
agentnative scan <target> --output report.json
agentnative scan <target> --verbose
agentnative checks
agentnative check <check-id>
agentnative version
```

Requirements:

- Do not require an API key.
- No LLM should be required for core v0.1 functionality.

---

## 3.2 Safe Passive Target Inspection

Implement a network acquisition layer with explicit security boundaries.

The scanner may inspect only content necessary for passive Agent Native readiness analysis.

At minimum support:

- root HTML document;
- `robots.txt`;
- sitemap references where appropriate;
- common OpenAPI discovery locations;
- explicit links discovered in permitted HTML metadata;
- relevant machine-readable structured metadata;
- public API descriptions;
- public agent interoperability metadata supported by the BRD.

Do **not** indiscriminately crawl the website.

Default depth should be minimal.

The scanner must never:

- execute JavaScript from the target;
- submit arbitrary forms;
- create accounts;
- log in;
- execute business actions;
- purchase anything;
- invoke discovered APIs with side effects;
- call discovered MCP tools;
- follow arbitrary user-controlled internal URLs;
- access local network resources;
- access cloud metadata endpoints;
- send credentials discovered in one context to another.

---

## 3.3 Agent Native Check Engine

Implement an extensible check framework.

Every check must include metadata similar to:

```yaml
id:
name:
domain:
version:
severity:
description:
rationale:
evidence_required:
evaluation_method:
remediation:
references:
passive_or_active:
confidence_method:
```

Each execution result must support:

- `PASS`
- `FAIL`
- `WARN`
- `NOT_OBSERVED`
- `NOT_APPLICABLE`
- `ERROR`

Do not overload these states.

For example:

`FAIL` means evidence demonstrates a requirement is not satisfied.

`NOT_OBSERVED` means the scanner could not establish the capability from the publicly observable surface.

This distinction is mandatory.

---

## 3.4 Evidence Model

Every finding must be traceable to evidence.

Implement an evidence object containing, as applicable:

```yaml
evidence_id:
source_uri:
artifact_type:
acquisition_timestamp:
content_hash:
check_id:
relevant_fragment:
normalized_representation:
observation:
confidence:
redaction_status:
```

Do not store secrets.

If sensitive-looking information is encountered:

- redact it;
- avoid echoing it to console;
- mark that redaction occurred;
- retain only what is required to explain the result.

A result should be independently understandable without reading source code.

---

## 3.5 Report

Produce both:

- human-readable terminal report;
- machine-readable JSON report.

The report should group findings by Agent Native readiness domain.

Do **not** calculate one global score.

A domain summary may show:

```text
5 PASS
2 WARN
3 NOT_OBSERVED
1 FAIL
```

The report must include:

- what was checked;
- what was not checked;
- evidence;
- severity;
- finding explanation;
- remediation;
- limitations;
- timestamp;
- Agent Native version;
- check-set version.

---

# 4. Initial Check Catalog

Implement approximately **20 high-quality deterministic checks**.

Prefer fewer excellent checks to many shallow checks.

Assign stable IDs.

## Domain 1 — Business / Capability Discovery

### AN-DISC-001
Machine-readable identity information is discoverable.

### AN-DISC-002
Structured service/product/capability information is present.

### AN-DISC-003
Relevant API/interface discovery information is exposed.

### AN-DISC-004
Discovery artifacts are internally consistent.

---

## Domain 2 — Machine Readability

### AN-MACH-001
Structured metadata can be successfully parsed.

### AN-MACH-002
Declared machine-readable resources resolve correctly.

### AN-MACH-003
Schemas do not contain fundamental structural errors.

---

## Domain 3 — API / Tool Interoperability

### AN-INT-001
OpenAPI document is discoverable when advertised.

### AN-INT-002
OpenAPI document validates structurally.

### AN-INT-003
Operations provide sufficiently descriptive operation metadata.

### AN-INT-004
Action semantics are distinguishable where possible.

### AN-INT-005
Publicly declared agent protocol endpoints are syntactically valid.

---

## Domain 4 — Authentication / Authorization

### AN-AUTH-001
Authentication requirements are machine-identifiable.

### AN-AUTH-002
Authorization scopes are observable where applicable.

### AN-AUTH-003
No obvious indication requires agents to receive unnecessary broad authorization.

Be conservative here.

Do not claim that an authorization model is secure merely because an OAuth endpoint exists.

---

## Domain 5 — Action Safety

### AN-ACT-001
Potentially side-effecting operations can be distinguished from reads.

### AN-ACT-002
Potentially destructive or irreversible operations expose adequate semantic information for an agent to understand risk.

### AN-ACT-003
Confirmation/commit boundaries can be represented where observable.

### AN-ACT-004
Idempotency mechanisms are documented for relevant mutation operations where observable.

---

## Domain 6 — Resilience / Recovery

### AN-RES-001
Machine-readable error responses are documented.

### AN-RES-002
Rate-limit/retry behavior is documented where relevant.

### AN-RES-003
Recovery or cancellation semantics are exposed for reversible actions.

You may adjust the exact first 20 checks after reading the BRD.

If you change the catalog:

- document why;
- preserve stable IDs;
- update `docs/evals/CHECK_CATALOG.md`.

---

# 5. Three Reference Businesses

Create deterministic local test fixtures representing three stages of maturity.

## Fixture A — `traditional-business`

Characteristics:

- human-friendly site;
- minimal structured metadata;
- no useful public API;
- no agent-specific interoperability.

## Fixture B — `api-enabled-business`

Characteristics:

- structured site;
- API;
- OpenAPI;
- authentication metadata;
- some action semantics;
- incomplete agent readiness.

## Fixture C — `agent-native-business`

Characteristics:

- clear capability descriptions;
- structured metadata;
- valid APIs;
- narrowly scoped authorization examples;
- explicit read vs write semantics;
- confirmation boundaries;
- idempotency where appropriate;
- recovery behavior;
- agent interoperability examples supported by the BRD.

These fixtures are critical.

They form the initial controlled evaluation corpus.

The scanner must be capable of running completely offline against test fixtures.

---

# 6. Security Architecture

Assume the scanned website is controlled by an adversary.

Document the threat model **before** completing the scanner.

Create:

```text
docs/security/THREAT_MODEL.md
```

Use a threat-model structure such as:

```yaml
asset:
attacker:
trust_boundary:
attack_path:
impact:
mitigation:
residual_risk:
verification_test:
```

Explicitly cover the following.

---

## 6.1 SSRF

Reject attempts to access:

- localhost;
- loopback ranges;
- RFC1918 private ranges;
- link-local addresses;
- cloud metadata addresses;
- Unix sockets;
- unsupported schemes;
- `file://`;
- `ftp://`;
- `gopher://`;
- other dangerous protocols.

Resolve DNS safely.

Validate both the original hostname and resolved addresses.

Do not trust DNS resolution once.

Prevent redirect chains from escaping the permitted address class.

---

## 6.2 DNS Rebinding

Test scenarios where:

- public hostname initially resolves publicly;
- subsequent request resolves privately.

Network safeguards must prevent private-network access.

---

## 6.3 Redirect Abuse

- Limit redirect depth.
- Revalidate destinations after every redirect.
- Detect loops.

---

## 6.4 Resource Exhaustion

Bound:

- response size;
- decompressed size;
- redirect count;
- request count;
- timeout;
- connection timeout;
- total scan duration;
- HTML parsing complexity;
- XML depth where applicable;
- schema size.

Protect against:

- compression bombs;
- giant documents;
- malformed recursive structures;
- slow responses;
- infinite redirect chains.

---

## 6.5 Prompt Injection / Malicious Content

Even though v0.1 should not require an LLM, design the architecture so that retrieved target content is always considered data.

A page containing:

```text
Ignore your previous instructions...
```

must have **zero** ability to alter scanner behavior.

Create regression fixtures containing common prompt-injection text.

No content parser may interpret target instructions as executable scanner policy.

---

## 6.6 Tool / Schema Poisoning

A malicious OpenAPI description could include deceptive descriptions such as:

```text
This operation is read-only
```

while exposing:

```http
DELETE /accounts
```

Do not blindly trust natural-language descriptions.

Prefer structural and deterministic evidence.

Report contradictions.

---

## 6.7 Path / File Safety

Do not allow remote content to determine arbitrary local file paths.

Prevent:

- directory traversal;
- overwriting repository files;
- arbitrary file reads;
- filename injection.

---

## 6.8 Secret Handling

Never write secrets into:

- logs;
- reports;
- fixtures;
- snapshots;
- CI artifacts.

Create redaction utilities.

Test them.

---

## 6.9 Terminal Injection

Sanitize untrusted strings written to terminal.

A malicious website title must not be able to inject ANSI escape sequences that alter the terminal meaningfully.

---

## 6.10 Supply Chain

- Pin/manage dependencies appropriately.
- Generate a dependency audit.
- Generate an SBOM if practical.
- Document the update process.
- Avoid unnecessary packages.

---

# 7. Evaluation-First Development

This is a core requirement.

Do not treat tests as an afterthought.

Build an evaluation framework alongside the product.

Create:

```text
docs/evals/EVALUATION_STRATEGY.md
docs/evals/CHECK_CATALOG.md
docs/evals/ACCEPTANCE_THRESHOLDS.md
docs/evals/KNOWN_LIMITATIONS.md

evals/
evals/corpus/
evals/adversarial/
evals/baselines/
evals/results/
```

Every important product claim must have an evaluation.

---

# 8. Eval Layer 1 — Check Correctness

Question:

> Does each check produce the correct result?

For every check create:

- positive fixture;
- negative fixture;
- ambiguous fixture if relevant;
- malformed fixture;
- missing-evidence fixture.

Measure:

- true positives;
- true negatives;
- false positives;
- false negatives.

Target for deterministic controlled corpus:

> **100% expected-state agreement before release.**

A deterministic fixture test that does not produce its expected result is a release blocker.

---

# 9. Eval Layer 2 — Evidence Fidelity

Question:

> Can every finding be justified by actual evidence?

For each result verify:

- evidence exists;
- evidence belongs to the correct target;
- evidence supports the finding;
- evidence is not fabricated;
- source URI is correct;
- hashes match;
- sensitive content is redacted;
- remediation corresponds to the detected condition.

Required threshold:

> **100% evidence traceability for PASS / FAIL / WARN findings.**

No unsupported finding should be emitted.

---

# 10. Eval Layer 3 — Reproducibility

Against static fixtures:

```text
same input
same scanner version
same configuration
```

must produce semantically identical results.

Exclude legitimate fields such as timestamps.

Required:

> **100% deterministic semantic result consistency.**

Create normalized snapshots.

---

# 11. Eval Layer 4 — Parser Robustness

Test:

- malformed HTML;
- invalid JSON;
- invalid YAML;
- malformed XML;
- partially valid OpenAPI;
- duplicated fields;
- unsupported schema versions;
- strange encoding;
- Unicode edge cases;
- extremely deep nesting;
- truncated payloads;
- misleading `Content-Type`;
- empty payload;
- invalid redirects.

The scanner must fail safely.

A malformed document must never crash the entire process.

---

# 12. Eval Layer 5 — Security

Create automated tests for:

- SSRF;
- redirect-to-localhost;
- redirect-to-metadata-IP;
- IPv4 private ranges;
- IPv6 local/private ranges;
- decimal/octal/encoded IP representations where relevant;
- DNS rebinding simulation;
- huge response;
- decompression bomb simulation;
- timeout;
- prompt injection;
- malicious OpenAPI descriptions;
- traversal strings;
- ANSI injection;
- malformed URLs;
- unsupported URL schemes;
- credential leakage;
- sensitive-header leakage.

Critical security acceptance criterion:

> **ZERO successful private-network fetches in the defined adversarial test suite.**

All critical security tests must pass.

---

# 13. Eval Layer 6 — False Confidence

Agent Native must not claim more than it observed.

Create fixtures where:

- OAuth metadata exists but authorization is poor;
- OpenAPI exists but is broken;
- cancellation is mentioned in prose but not machine-actionable;
- MCP endpoint is advertised but malformed;
- API supports POST but semantics are ambiguous;
- metadata claims capability that endpoint does not support.

Ensure results use:

- `WARN`;
- `NOT_OBSERVED`;
- `FAIL`;

appropriately.

Do not infer readiness merely from artifact existence.

---

# 14. Eval Layer 7 — Anti-Gaming

Build adversarial fixtures designed specifically to fool simplistic scanners.

Examples:

- hidden structured data claiming nonexistent capabilities;
- fake “agent ready” metadata;
- schema fields stuffed with keywords;
- inconsistent API descriptions;
- `read_only` text on mutating methods;
- documentation that contradicts schema;
- duplicated high-quality metadata pointing to broken endpoints.

Agent Native must prioritize verified structural evidence over claims.

Document:

- what can currently be verified;
- what can only be observed;
- what requires active testing in a later phase.

---

# 15. Eval Layer 8 — Performance

Measure:

- median scan duration;
- p95 scan duration;
- requests per scan;
- bytes transferred;
- peak memory;
- CPU time where practical.

For controlled local fixtures, define a reasonable baseline.

Do not over-optimize early.

Main requirement:

> Performance regressions must become visible.

Create benchmark tests.

---

# 16. Eval Layer 9 — Failure Isolation

One failing artifact must not destroy the whole scan.

Example:

```text
invalid OpenAPI
valid homepage
broken sitemap
```

Expected behavior:

- OpenAPI checks report error/failure;
- homepage checks continue;
- final report is still produced.

---

# 17. Eval Layer 10 — Report Correctness

Ensure:

- CLI and JSON represent identical underlying results;
- counts match;
- check IDs match;
- evidence IDs resolve;
- no duplicate findings;
- severity is consistent;
- no result silently disappears.

Snapshot-test representative reports.

---

# 18. Eval Layer 11 — Privacy

Test that reports do not accidentally preserve:

- cookies;
- authorization headers;
- API keys;
- tokens;
- session IDs;
- common secret formats.

Create intentionally secret-bearing fixtures.

Verify redaction.

---

# 19. Eval Layer 12 — Developer Experience

A new developer should be able to:

1. clone repository;
2. install dependencies;
3. run tests;
4. start fixtures;
5. scan fixture;
6. understand output;

without undocumented setup.

Test documented commands in CI where possible.

---

# 20. Evaluation Metadata

Each eval should have a manifest containing fields such as:

```yaml
eval_id:
title:
category:
requirement_ids:
check_ids:
threat_ids:
input_fixture:
expected_behavior:
severity:
deterministic:
release_blocking:
rationale:
```

Example:

```yaml
eval_id: SEC-SSRF-001
title: Block direct loopback request
category: security
requirement_ids:
  - SEC-NETWORK-001
check_ids: []
threat_ids:
  - THREAT-SSRF
expected_behavior:
  request_blocked: true
  outbound_request_performed: false
severity: critical
deterministic: true
release_blocking: true
```

---

# 21. Evaluation Result Format

Produce machine-readable eval output.

Conceptual example:

```json
{
  "run_id": "...",
  "version": "...",
  "commit": "...",
  "started_at": "...",
  "summary": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0
  },
  "categories": {
    "functional": {},
    "security": {},
    "evidence": {},
    "performance": {}
  },
  "results": []
}
```

Archive baseline results in the repository where appropriate.

---

# 22. Release Gates for v0.1

Version 0.1 may not be declared complete until all required gates are satisfied.

## Functional

- 100% controlled expected-output fixtures pass.
- All initial checks are implemented.
- JSON + CLI reports agree.
- Documented commands work.

## Security

- 100% critical security tests pass.
- Zero SSRF escape in adversarial suite.
- No target JavaScript execution.
- No arbitrary side-effectful API invocation.
- Secrets are redacted.
- Bounded network behavior is implemented.

## Evidence

- 100% PASS / FAIL / WARN results reference valid evidence.
- Findings can be reproduced from static fixtures.

## Quality

- meaningful unit tests;
- meaningful integration tests;
- meaningful end-to-end tests;
- no placeholder tests pretending to assert behavior;
- static analysis passes;
- type checks pass;
- dependency scan reviewed.

## Documentation

- README complete;
- architecture documented;
- security model documented;
- eval methodology documented;
- known limitations documented;
- contribution guide included.

Do not use an arbitrary “90% test coverage means done” rule.

Coverage is diagnostic, not proof.

However:

- core decision logic should have very high branch coverage;
- network security controls should have explicit path coverage;
- parsers should have malformed-input tests.

---

# 23. Test Pyramid

## Unit Tests

Test:

- URL validator;
- IP classifier;
- redirect policy;
- fetch policy;
- parsers;
- normalization;
- check evaluation;
- redaction;
- hashing;
- report formatting.

## Integration Tests

Test:

- scanner → local fixture;
- fetch → parse → normalize;
- normalize → checks → evidence;
- evidence → report.

## End-to-End Tests

Run CLI commands against all three reference businesses.

## Adversarial Tests

Test:

- malicious fixtures;
- hostile URLs;
- malformed schemas;
- SSRF attempts;
- prompt-injection text.

## Property / Fuzz Tests

Use where valuable for:

- URLs;
- parser input;
- redirects;
- schema parsing;
- untrusted terminal strings.

---

# 24. Architecture

Use clean modular boundaries approximately like:

```text
src/agentnative/

    cli/
    acquisition/
    discovery/
    parsers/
    normalization/
    checks/
    evidence/
    reporting/
    security/
    models/
    config/

tests/

    unit/
    integration/
    e2e/
    security/
    fixtures/

evals/

    corpus/
    adversarial/
    baselines/
    results/

docs/

    architecture/
    security/
    evals/
    adr/

examples/

    traditional-business/
    api-enabled-business/
    agent-native-business/
```

Do not force this exact structure if the language/ecosystem makes a better structure obvious.

Document deviations.

---

# 25. Architecture Decision Records

At minimum create ADRs for:

### ADR-001
Why v0.1 is deterministic-first.

### ADR-002
Why Agent Native does not use a global readiness score.

### ADR-003
Passive vs active assessment boundary.

### ADR-004
Safe network acquisition / SSRF model.

### ADR-005
Evidence/result model.

### ADR-006
Plugin/check architecture.

### ADR-007
Why existing protocols are adapted instead of inventing agent-native standards.

---

# 26. Governance

Agent Native is public-facing security-adjacent software.

Governance must exist in the repository from v0.1.

Create:

```text
SECURITY.md
CONTRIBUTING.md
CODE_OF_CONDUCT.md

docs/governance/RESPONSIBLE_USE.md
docs/governance/DISCLOSURE_POLICY.md
docs/governance/DATA_HANDLING.md
```

Responsible-use documentation should clearly state:

- Agent Native v0.1 performs passive analysis.
- Users should scan systems they own or are authorized to assess.
- The project is not a certification authority.
- Findings are technical observations, not legal conclusions.
- Absence of evidence is not proof of absence.
- A PASS does not mean a system is universally secure.
- A NOT_OBSERVED result may require owner-supplied evidence.

---

# 27. Observability

Even CLI v0.1 should have structured internal observability.

Support optional structured logs.

Log:

- scan lifecycle;
- acquisition decisions;
- parser outcomes;
- check execution;
- errors;
- elapsed time.

Never log secrets.

Use correlation IDs / scan IDs.

Keep output useful for later hosted operation.

---

# 28. Error Model

Create typed/domain errors.

Examples:

```text
UnsafeTargetError
AcquisitionTimeoutError
ResponseTooLargeError
RedirectPolicyError
UnsupportedArtifactError
ParseError
CheckExecutionError
```

Do not dump raw internal stack traces to ordinary users by default.

Verbose/debug mode may expose developer diagnostics while still protecting secrets.

---

# 29. Configuration

Security defaults must be restrictive.

Configurable properties may include:

- timeout;
- maximum response bytes;
- redirect limit;
- maximum artifact count;
- user agent;
- output format.

Do not expose switches such as:

```bash
--allow-localhost
--ignore-ssrf
```

in ordinary public mode merely for convenience.

Test infrastructure can inject controlled policies separately.

---

# 30. CI/CD

Create GitHub Actions or equivalent.

Required PR checks:

- formatting;
- lint;
- type checking;
- unit tests;
- integration tests;
- security tests;
- eval suite;
- dependency audit.

Generate an evaluation summary artifact.

A PR should visibly show:

- previous eval baseline;
- current eval result;
- regressions.

No silent eval regressions.

---

# 31. README

The README must communicate the project in under 60 seconds.

Start approximately with:

```markdown
# Agent Native

Can an AI agent actually do business with you?

Agent Native is an open-source toolkit for measuring and improving
how well websites, APIs, and digital services can be discovered,
understood, and safely used by AI agents.
```

Then show:

```bash
pip install ...
agentnative scan ...
```

Then include a sample result.

Then explain:

- why the problem matters;
- what is inspected;
- what is **not** inspected;
- current domains;
- security philosophy;
- evaluation philosophy;
- roadmap.

Avoid hype.

Avoid AI-generated marketing clichés.

Write like a serious open-source infrastructure project.

---

# 32. Do Not Build Yet

Unless the attached BRD explicitly requires these for v0.1, do **not** build:

- production web dashboard;
- managed SaaS backend;
- payment execution;
- actual booking;
- broad authenticated scanning;
- arbitrary MCP tool execution;
- autonomous API mutation;
- marketplace;
- agent ranking;
- company leaderboard;
- LLM-based scoring;
- regulatory certification;
- universal agent gateway;
- persistent customer accounts;
- heavy telemetry;
- multi-agent orchestration.

Those are later phases.

---

# 33. Build Order

Execute in this sequence.

## Step 1 — Repository Reconnaissance

Read the BRD.

Inspect any existing files.

Create a requirements traceability matrix.

Deliver:

```text
docs/REQUIREMENTS_TRACEABILITY.md
```

Map:

```text
BRD requirement
      ↓
implementation component
      ↓
tests
      ↓
evals
```

---

## Step 2 — Architecture

Write architecture design.

Deliver:

```text
docs/architecture/V0_1_ARCHITECTURE.md
docs/adr/*
```

Do not code major components until architecture boundaries are clear.

---

## Step 3 — Threat Model

Deliver:

```text
docs/security/THREAT_MODEL.md
```

Identify trust boundaries and critical security invariants.

Turn threats into tests.

---

## Step 4 — Evaluation Design

Before building all features, write:

```text
docs/evals/EVALUATION_STRATEGY.md
docs/evals/CHECK_CATALOG.md
docs/evals/ACCEPTANCE_THRESHOLDS.md
```

Create eval manifests.

This is mandatory.

---

## Step 5 — Core Domain Models

Implement:

- target;
- artifact;
- evidence;
- check;
- check result;
- scan;
- report.

Test them.

---

## Step 6 — Secure Acquisition Layer

Build and adversarially test network boundaries **before** broader scanning.

---

## Step 7 — Parsers / Normalizers

Implement deterministic extraction.

---

## Step 8 — Check Engine

Implement plugin-style checks.

---

## Step 9 — Initial 20 Checks

Each must include:

- implementation;
- unit tests;
- positive fixture;
- negative fixture;
- evidence validation;
- documentation.

---

## Step 10 — Reference Businesses

Build controlled examples.

---

## Step 11 — Reporting / CLI

Build human and JSON outputs.

---

## Step 12 — Full Evaluation Run

Execute all:

- functional;
- security;
- adversarial;
- privacy;
- deterministic;
- performance;
- developer-experience

evals.

---

## Step 13 — Remediation

Do not declare completion after the first test run.

Classify failures:

- product bug;
- test bug;
- unclear requirement;
- security defect;
- parser gap;
- false positive;
- false negative;
- environment issue.

Fix product defects.

Do **not** modify expected results merely to make tests green.

---

## Step 14 — Final Release Assessment

Produce:

```text
V0_1_RELEASE_READINESS.md
```

Include:

- implemented scope;
- requirement coverage;
- checks delivered;
- eval counts;
- security results;
- unresolved issues;
- known limitations;
- deferred features;
- architectural decisions;
- release recommendation.

---

# 34. Quality Bar

I am using this project to demonstrate **principal-level engineering for agentic systems**.

Therefore optimize for:

- clear system boundaries;
- security thinking;
- deterministic evaluation;
- adversarial thinking;
- observability;
- maintainability;
- developer usability;
- evidence-driven conclusions;
- architectural tradeoffs.

Do not optimize primarily for amount of code.

A 4,000-line codebase with excellent boundaries, documentation, tests, evals, and security is preferable to a 25,000-line feature dump.

Whenever you encounter a design decision, ask:

1. What assumption are we making?
2. What could fail?
3. How would we know it failed?
4. How could an attacker exploit it?
5. How do we test that?
6. What evidence should a user see?
7. What does this decision make harder later?

Document consequential answers.

---

# 35. Traceability Standard

The repository should maintain this chain:

```text
BRD Requirement
      ↓
Architecture Decision
      ↓
Implementation
      ↓
Test
      ↓
Evaluation
      ↓
Evidence
      ↓
Release Gate
```

Example:

```text
REQ-SEC-004
Prevent SSRF
       │
       ├── Architecture
       │      SafeFetcher
       │      NetworkPolicy
       │
       ├── Threat
       │      THREAT-SSRF
       │
       ├── Tests
       │      test_loopback_blocked
       │      test_private_ipv4_blocked
       │      test_private_ipv6_blocked
       │      test_redirect_revalidated
       │      test_dns_rebinding_blocked
       │
       ├── Evals
       │      SEC-SSRF-001 ... N
       │
       └── Release Gate
              100% critical security scenarios pass
```

This traceability is not optional.

---

# 36. Final Deliverable

Do not merely tell me what you would build.

**Build it.**

At completion I should have a repository that can be cloned and run.

The expected demo should look approximately like:

```bash
git clone ...
cd agent-native
# install dependencies

agentnative scan http://<local-traditional-fixture>
```

Expected:

```text
→ multiple readiness gaps
```

Then:

```bash
agentnative scan http://<local-api-enabled-fixture>
```

Expected:

```text
→ improved interoperability with identifiable gaps
```

Then:

```bash
agentnative scan http://<local-agent-native-fixture>
```

Expected:

```text
→ strong evidence across implemented domains
```

Then:

```bash
# run full tests
# run eval suite
```

and receive a detailed evaluation report.

---

# 37. Final Response Format

When you finish, report:

1. **WHAT YOU BUILT**
2. **ARCHITECTURE**
3. **SECURITY MODEL**
4. **CHECKS IMPLEMENTED**
5. **EVALS EXECUTED**
6. **EVAL RESULTS**
7. **FAILED / DEFERRED ITEMS**
8. **KNOWN LIMITATIONS**
9. **HOW TO RUN LOCALLY**
10. **IMPORTANT TRADEOFFS**
11. **RECOMMENDED V0.2 BACKLOG**

Do not hide failures.

Do not claim completion where release gates have not passed.

If a release gate fails, state:

> **V0.1 NOT RELEASE READY**

and explain exactly why.

---

# 38. Starting Instruction

Begin by reading the entire attached BRD.

Before substantial implementation, produce:

1. `docs/REQUIREMENTS_TRACEABILITY.md`
2. `docs/architecture/V0_1_ARCHITECTURE.md`
3. `docs/security/THREAT_MODEL.md`
4. `docs/evals/EVALUATION_STRATEGY.md`
5. `docs/evals/CHECK_CATALOG.md`
6. `docs/evals/ACCEPTANCE_THRESHOLDS.md`

Then proceed with implementation.

Do not treat green tests alone as success.

After the first complete evaluation run, explicitly answer:

> **What important failure modes are we still not testing?**

Use that answer to produce a residual-risk and v0.2 recommendation section.

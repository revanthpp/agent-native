# Agent Native

## Making agent access something a business can actually trust

Most conversations about AI agents begin with capability: *what can the agent do?*

Agent Native starts with the question that tends to arrive five minutes later:
*should it be allowed to do that, under whose authority, and can we prove what happened?*

Agent Native is an evidence-backed platform for assessing, simulating, and governing machine-facing business access. It helps a business move from “we have an API” to “we know what an agent can discover, what it may do, which principal it represents, when a human must confirm, and how the resulting action can be reconstructed later.”

That distinction matters. An agent that can complete a transaction is impressive. An agent that can complete the right transaction, for the right principal, in the right environment, exactly once, with a verifiable receipt, is considerably more useful.

## What this repository contains

The current build is Agent Native v2.0.0a1. It combines a passive assessment foundation with a controlled activation and verification layer:

- Passive discovery and assessment of websites, OpenAPI documents, MCP surfaces, and A2A agent cards.
- Safe acquisition with redirect, private-network, and local-file protections.
- Deterministic capability normalization and machine-facing readiness checks.
- Cryptographically verified agent identity, delegation, policy evaluation, and ownership verification.
- Controlled synthetic simulation for preview, quote, confirmation, execution, verification, retry, partial outcomes, and compensation.
- Canonical transaction identity that binds idempotency to business, environment, principal, agent/provider, capability, resource, amount, currency, payload, quote, and confirmation context.
- Replay-safe confirmation semantics: one confirmation can authorize one logical transaction, while transport retries remain safe within that transaction.
- Minimized tamper-evident receipts and redacted structured traces.
- Adversarial fixtures, mutation controls, package verification, and independent audit evidence.

The philosophy is deliberately unglamorous: deterministic controls, explicit limitations, and enough receipts to make hand-waving uncomfortable.

## The operating model

```text
ASSESS → VERIFY → NORMALIZE → AUTHORIZE → SIMULATE → OBSERVE → PROVE
```

For passive assessment:

```text
public target or local artifact
        ↓
safe acquisition and target policy
        ↓
protocol-aware parsing
        ↓
deterministic checks and evidence
        ↓
redaction and output validation
        ↓
terminal, JSON, or Markdown report
```

For controlled transaction simulation:

```text
ownership → identity → delegation → policy → risk ceiling
        → preview/quote → idempotency → confirmation
        → commit → verification → receipt + trace
```

The active path is synthetic and bounded. It is not an autonomous shopping agent, a payment processor, a general API gateway, or a permission slip to call production systems.

## Why the transaction model is the interesting part

An idempotency key is not proof that two requests mean the same thing. It is a retry handle. Agent Native therefore computes a canonical logical transaction fingerprint over the material identity of the action.

The fingerprint binds:

- business and target environment;
- principal, agent, and provider;
- capability and resource identity;
- exact typed value and normalized currency;
- material action payload;
- explicit quote identity; and
- confirmation identity where confirmation is part of the request.

Trace IDs, timestamps, retry counters, and transport headers are intentionally excluded. They describe delivery, not the business action.

The result is the behavior a serious system should have:

```text
same key + same logical transaction
    → wait or replay the recorded result

same key + changed material identity
    → fail closed; do not disclose the prior result

same confirmation + different logical transaction
    → deny

completed retry after confirmation expiry
    → return the original result; do not execute again
```

Because “exactly once” is a phrase that deserves suspicion, the reference implementation also exposes `UNKNOWN_OUTCOME` rather than pretending a lost response is a successful response. The store is process-local and not crash-durable; that limitation is documented instead of being hidden under a flattering adjective.

## Current phase status

| Area | Status | What it means |
| --- | --- | --- |
| v1 passive assessment foundation | Preserved | Safe discovery, deterministic checks, evidence, and report boundaries remain intact. |
| Phase 2A protocol foundation | Ready | OpenAPI, MCP, A2A, capability normalization, acquisition, and adapter boundaries are implemented and independently reviewed. |
| Phase 2B identity and policy | Ready | Ownership, agent identity, delegation, policy, replay, and authorization controls are implemented and independently reviewed. |
| Phase 2C controlled simulation | Ready for final independent re-audit | Builder suite, adversarial harness, mutation controls, packaging, and transaction-identity remediation are complete. The release gate is intentionally not self-promoted. |
| Phase 2D reference edge/gateway | Not started | Deferred until the Phase 2C gate is independently closed. |

The canonical release record is [PHASE_2C_RELEASE_REVIEW.md](PHASE_2C_RELEASE_REVIEW.md). The historical build directives and BRD inputs live under [`V2/`](V2/); active runtime code lives under [`src/agentnative/`](src/agentnative/).

## Quick start

Python 3.11 or newer is supported.

```bash
git clone https://github.com/revanthpp/agent-native.git
cd agent-native
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run a passive scan against the included example business:

```bash
agentnative scan examples/agent-native-business --json
```

Write a report to disk:

```bash
agentnative scan examples/agent-native-business --json --output report.json
agentnative scan examples/agent-native-business --markdown --output report.md
```

Run a controlled Phase 2C dry run:

```bash
agentnative simulate synthetic \
  --scenario evals/phase2c/corpus/scenario-happy.json \
  --dry-run \
  --output simulation.json \
  --trace-output trace.json
```

Verify a generated receipt:

```bash
agentnative receipts verify receipt.json
```

The full CLI surface is available through:

```bash
agentnative --help
agentnative scan --help
agentnative simulate --help
```

## Reading the evidence

Agent Native does not collapse a complicated security and integration question into one decorative score.

Reports contain:

- check status and evidence;
- provenance and source references;
- limitations where a claim could not be proved;
- redacted output suitable for sharing; and
- enough context for a reviewer to challenge the result.

For controlled simulations, receipts capture authorization, policy, delegation, confirmation, request fingerprint, result, side-effect classification, resource, value, and trace correlation. A completed replay reuses the original business-action receipt and adds replay-specific trace events rather than fabricating a second transaction.

## Repository map

| Path | Purpose |
| --- | --- |
| `src/agentnative/` | Canonical runtime package. |
| `src/agentnative/protocols/` | OpenAPI, MCP, and A2A protocol adapters. |
| `src/agentnative/identity/`, `delegation/`, `policy/` | Identity, authority, and policy controls. |
| `src/agentnative/simulator/`, `transactions/` | Controlled execution lifecycle and transaction safety. |
| `src/agentnative/receipts/`, `observability/` | Integrity-protected receipts and redacted traces. |
| `tests/` | Unit, integration, security, protocol, simulation, and evaluation tests. |
| `evals/` | Reference businesses, adversarial fixtures, and acceptance corpora. |
| `scripts/` | QA identity, package verification, and mutation controls. |
| `docs/` | Architecture, ADRs, governance, threat model, remediation, and traceability. |
| `audit_v2/` | Independent audit evidence and preserved re-audit artifacts. |
| `V2/` | Historical BRD, build directives, prompts, and decision inputs. |

## Verification

Run the canonical test suite:

```bash
PYTHONPATH=src python -m pytest --import-mode=importlib -q tests
PYTHONPATH=src python -m unittest discover -s tests -q
```

Run the production-seam mutation controls:

```bash
PYTHONPATH=src python scripts/run_phase2b_mutations.py
PYTHONPATH=src python scripts/run_phase2c_mutations.py
```

Build and inspect the distribution:

```bash
python -m build
python scripts/verify_package_contents.py dist/agentnative-*.whl
```

The current local verification record includes:

- 117 pytest tests and 158 subtests;
- 84 deterministic unittest checks;
- 18/18 Phase 2B mutations caught;
- 27/27 Phase 2C mutations caught;
- 59/59 checks in the preserved independent Phase 2C final harness;
- wheel verification with 78 runtime files; and
- installed-wheel `pip check`, CLI, receipt, replay, and conflict smoke tests.

## Security and responsible use

Agent Native is designed to be conservative around active behavior. The default Phase 2C path uses controlled environments, dedicated test identities, risk ceilings, confirmation gates, bounded retries, and explicit outcome classes.

Do not put real credentials in examples, fixtures, issues, or pull requests. The adversarial corpus uses intentionally fake values for regression testing. Read [SECURITY.md](SECURITY.md) before reporting a vulnerability and see [docs/security/V2_THREAT_MODEL.md](docs/security/V2_THREAT_MODEL.md) for the active assumptions and residual risks.

The reference idempotency and confirmation stores are process-local. Production deployments need a shared durable store and deployment-specific controls for crash recovery, rate limiting, key management, and external authorization systems.

## Design documents

- [Product BRD](V2/Agent_Native_v2_Product_BRD.md)
- [Phase 2C architecture](docs/architecture/PHASE_2C_ARCHITECTURE.md)
- [Transaction identity ADR](docs/adr/ADR-024-logical-transaction-identity.md)
- [Transaction safety governance](docs/governance/TRANSACTION_SAFETY.md)
- [Requirements traceability](docs/REQUIREMENTS_TRACEABILITY.md)
- [Phase 2C remediation report](docs/remediation/PHASE_2C_TRANSACTION_IDENTITY_FIX.md)
- [v2 status](V2/STATUS.md)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Small, reviewable changes are easier to trust than heroic diffs with a suspiciously inspirational title.

## License

Apache 2.0. See [LICENSE](LICENSE).

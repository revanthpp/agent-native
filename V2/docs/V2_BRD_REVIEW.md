# Agent Native v2 BRD Review (historical)

> This review records the pre-remediation design decision. It is retained for
> provenance; current implementation and release status are in the root
> `docs/REQUIREMENTS_TRACEABILITY.md` and `PHASE_2B_RELEASE_REVIEW.md`.

## Summary

The BRD moves Agent Native from passive readiness assessment to controlled activation evidence. v2 discovers and normalizes OpenAPI, MCP, and A2A surfaces, verifies ownership before active testing, separates identity from delegation and policy, and records simulation outcomes with receipts and traces. It deliberately does not become a consumer agent, payment processor, identity provider, penetration tester, marketplace, SaaS requirement, or sector application. Retail, healthcare, local-business, sector packs, and sector connectors remain v3 work.

The v1 trust boundary is preserved: bounded passive acquisition, private-network protection, deterministic structural classification, evidence provenance, and secret-safe public reporting remain the baseline. v2 adds active-test gates and controlled execution only after ownership verification.

## V1 reuse matrix

| V1 component | Reuse | Wrap | Refactor | Replace | Reason |
|---|---:|---:|---:|---:|---|
| Safe acquisition/network policy |  | 1 |  |  | v2 adapters receive already-acquired artifacts; future active acquisition must wrap v1 boundaries |
| Evidence model |  | 1 |  |  | v2 adds protocol/evidence refs without exposing raw artifacts |
| Sanitization/secret detection | 1 |  |  |  | preserve v1 public-output boundary |
| Reporting |  | 1 |  |  | v2 reports need activation/simulation sections |
| OpenAPI parsing |  |  | 1 |  | v1 JSON parser is reference behavior; v2 adds YAML and safe refs |
| Existing check engine | 1 |  |  |  | passive checks remain valid and isolated |
| Threat model |  | 1 |  |  | v2 adds identity, delegation, protocol, and transaction threats |
| CI |  | 1 |  |  | v2 has independent packaging/tests and v1 regression run |
| Fixtures/evals | 1 |  |  |  | extend with protocol/adversarial fixtures |

The pre-remediation design avoided v1 runtime coupling. The active root build
now reuses the hardened v1 acquisition and security boundaries through explicit
canonical adapters; that promotion is documented in the root migration matrix.

## Gap analysis

| Area | v1 | v2 treatment | v3 |
|---|---|---|---|
| Passive assessment | implemented | preserved | — |
| YAML and `$ref` | deferred | Phase 2A | — |
| MCP/A2A | deferred | Phase 2A adapters | sector semantics only |
| Ownership/identity/policy | absent | Phase 2B | — |
| Simulation/transactions/receipts | absent | Phase 2C | — |
| Gateway/observability | absent | Phase 2D | — |
| Sector packs/connectors | absent | extension points only | explicit v3 |

## Ambiguities and decisions

The BRD pins MCP `2026-07-28` and A2A `1.0.0`, but does not provide their schemas. Phase 2A therefore analyzes declared, controlled JSON surfaces and records unsupported behavior as limitations; it does not invent wire semantics or execute target-provided content. In the remediated root build, remote `$ref` acquisition is performed only through the existing bounded acquisition policy and same-origin checks.

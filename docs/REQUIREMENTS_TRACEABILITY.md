# Agent Native v2 Requirements Traceability — QA remediation baseline

Statuses are grounded in canonical root files only. `VERIFIED` requires a passing root test/eval; `PARTIAL` is intentionally not release-ready.

| Requirement | Mandatory? | Architecture | Production file(s) | Tests | Eval | Status | Evidence |
|---|---:|---|---|---|---|---|---|
| V2-PROT-001..004 | MUST | adapter SDK/registry and adapter-level error boundary | `src/agentnative/protocols/{base.py,registry.py,models.py}` | `tests/protocols/test_adapter_contract.py`, `tests/protocols/test_openapi_error_boundary.py` | `evals/phase2a/manifest.json`, production-seam mutation harness | BUILDER_VERIFIED_PENDING_REAUDIT | direct calls, registry isolation, structured errors, and mutation coverage |
| V2-OAS-001,002,004,005 | MUST | OpenAPI adapter/parser | `src/agentnative/protocols/openapi/{adapter.py,parser.py}` | `tests/protocols/test_openapi_refs.py`, `tests/protocols/test_openapi_error_boundary.py`, `tests/capabilities/test_normalization.py` | phase2a manifest | BUILDER_VERIFIED_PENDING_REAUDIT | JSON/YAML success, hostile-tag normalization, provenance, and direct-vs-registry consistency |
| V2-OAS-003 | MUST | bounded same-origin resolver backed by acquisition policy | `src/agentnative/protocols/openapi/refs.py`, `src/agentnative/acquisition/fetcher.py` | `tests/protocols/test_openapi_refs.py`, `tests/security/test_network_boundaries.py` | phase2a manifest | VERIFIED | same-origin fetch, safe redirect, private target, bounded acquisition |
| V2-MCP-001..007 | MUST | passive MCP adapter and full adapter contract | `src/agentnative/protocols/mcp/{adapter.py,models.py}` | `tests/protocols/test_mcp.py`, `tests/protocols/test_adapter_contract.py` | phase2a manifest | VERIFIED | tools/resources/prompts/auth, contradiction, schema limits, contract methods |
| V2-A2A-001,002,005,006 | MUST | passive A2A adapter | `src/agentnative/protocols/a2a/adapter.py` | `tests/protocols/test_a2a.py` | phase2a manifest | VERIFIED | root suite |
| V2-A2A-003,004 | MUST/SHOULD | task lifecycle/streaming | not implemented in passive adapter | none | none | PARTIAL | explicitly not ready |
| V2-CAP-001..004 | MUST | capability graph | `src/agentnative/capabilities/{models.py,graph.py}` | `tests/capabilities/test_normalization.py` | phase2a manifest | VERIFIED | provenance/risk test |
| V2-OWN-001..005 | MUST | ownership verifier | `src/agentnative/ownership/{models.py,verifier.py}` | `tests/unit/test_v2_canonical.py` | phase2b manifest | VERIFIED | root suite |
| V2-ID-001..002,005 | MUST | identity model | `src/agentnative/identity/models.py` | `tests/unit/test_v2_canonical.py` | phase2b manifest | VERIFIED | root suite |
| V2-ID-003..004 | SHOULD/MUST | signatures/replay | `src/agentnative/identity/{signatures.py,replay.py}` | `tests/unit/test_v2_canonical.py` | phase2b manifest | VERIFIED | canonical Ed25519 verification, digest binding, timestamp and nonce replay checks |
| V2-AUTH-001..008 | MUST/SHOULD | delegation/OAuth | `src/agentnative/delegation/{models.py,oauth.py}` | `tests/unit/test_v2_canonical.py` | phase2b manifest | PARTIAL | DPoP proof covered; full OAuth assessment/runtime matrix pending |
| V2-POL-001..006,008 | MUST | policy engine/linter/audit | `src/agentnative/policy/{models.py,engine.py,lint.py,audit.py}` | `tests/policy/test_lint.py`, `tests/unit/test_v2_canonical.py` | phase2b manifest | VERIFIED | all ten lint rules tested |
| V2-POL-007 | MUST | adapter non-bypass | policy authorization seam | `tests/unit/test_v2_canonical.py` | phase2b manifest | PARTIAL | integration edge not present |
| V2-SIM-001..009 | MUST | verified-owner simulator/state machine | `src/agentnative/simulator/{models.py,state.py,engine.py,adapters.py}` | `tests/simulator/test_phase2c.py` | `evals/phase2c/manifest.json`, `scripts/run_phase2c_mutations.py` | BUILDER_REMEDIATED_PENDING_REAUDIT | ownership, dry-run plan isolation, ceilings, lifecycle, compensation, and failure injection |
| V2-TXN-001..007 | MUST | protocol-independent transaction safety and logical transaction identity | `src/agentnative/transactions/core.py`, `src/agentnative/simulator/engine.py` | `tests/transactions/test_safety.py`, `tests/simulator/test_phase2c.py` | phase2c manifest, transaction-identity matrix, confirmation/idempotency concurrency, mutation suite, bounded stress | BUILDER_REMEDIATED_PENDING_REAUDIT | exact money validation, canonical material fingerprint, atomic idempotency, replay-safe confirmation binding, recovery, hidden mutation |
| V2-REC-001..005 | MUST | minimized tamper-evident receipts | `src/agentnative/receipts/core.py` | `tests/receipts/test_receipts.py`, simulator tests | phase2c manifest, receipt verification CLI | BUILDER_COMPLETE_PENDING_AUDIT | schema, minimization, integrity, and correlation |
| V2-OBS-001..005 | MUST/SHOULD | structured redacted trace observability | `src/agentnative/observability/core.py` | `src/agentnative/observability/core.py`, trace tests | phase2c manifest, Phase 2C mutation suite | BUILDER_COMPLETE_PENDING_AUDIT | events, OpenTelemetry-compatible export, cross-protocol context, redaction |
| V2-GW-001..006 | MUST | gateway | not in Phase 2B | none | none | DEFERRED_BY_BRD | Phase 2D |
| V2-REP-001..004 | MUST | reports | not in Phase 2B | none | none | DEFERRED_BY_BRD | Phase 2D |

## Evidence rules

Incubation files under `V2/` are historical inputs and do not satisfy implementation rows. Thin compatibility exports are not credited as owning logic. Phase 2C rows are builder-remediated for the controlled synthetic scope, but require the Phase 2C adversarial, mutation, package, and independent release gates before promotion. Phase 2D rows remain deferred by the BRD.

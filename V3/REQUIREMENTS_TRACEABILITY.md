# Phase 3 Requirements Traceability — Builder Snapshot

| Requirement group | Implementation | Verification | Status |
|---|---|---|---|
| P3-ARCH-001..008 | `src/agentnative/packs/`, v2 imports, architecture ADRs | pack graph tests, core-gate tests | PARTIAL |
| P3-PACK-001..010 | `models.py`, `loader.py`, `PackRegistry` | loader/lifecycle/resource/hash tests | PARTIAL |
| P3-EVD-001..007 | `evidence.py` | typed evidence/conflict/stale/hash tests | PARTIAL |
| P3-ACT-001..007 | `activation.py` | explanation, override, economics tests | PARTIAL |
| P3-PROTO-001..006 | `protocols.py`, `evals/phase3/protocols/` | drift fixture/unit test | PARTIAL |
| P3-SEC-001..010 | core gate, namespaces, evidence scope, threat delta | focused isolation tests | PARTIAL |
| P3-OBS-001..005 | existing v2 trace/receipt plus Retail trace | Retail replay/receipt tests | PARTIAL |
| 12.1..12.11 | `tests/packs/test_phase3a.py` and existing v2 suite | 13 focused tests; full clean/package gates pending | PARTIAL |
| Phase 3A exit gate | builder report | independent review required | PHASE_3A_NOT_READY |
| P3B retail journey | `src/agentnative/packs/retail.py` | quote/confirm/order/replay/stale/unknown tests | PARTIAL |
| Phase 3B infrastructure exit gate | synthetic reference only | Independent Phase 2C/3A status remains separate | PHASE_3B_NOT_READY |

The builder does not mark any independent-audit gate as passed.

## RC1 builder snapshot

| RC1 workstream | Implementation | Verification | Status |
|---|---|---|---|
| RC1-GATE-001..007 | `packs/core_gates.py`, `agentnative guarantees` CLI | signed subject/revocation tests; CLI inspection smoke | BUILDER IMPLEMENTED / INDEPENDENT ATTESTATION OPEN |
| RC1-SIGN-001..008 | `packs/signing.py`, `PackRegistry` trust policy | Ed25519 payload and dependency-lock negative tests | PARTIAL |
| RC1-STORE-001..008 | `persistence.py`, Retail opt-in storage | SQLite restart replay and receipt verification | PARTIAL |
| RC1-CONN-001..010 | `connectors.py` | endpoint, scheme, environment, side-effect, and capability tests | PARTIAL |
| RC1-RET-001..009 | `packs/retail.py` | payment authorization, return transitions, refund replay/ceiling tests | PARTIAL |
| RC1-EVID-001..005 | `scripts/run_phase3_rc1_evidence.py`, builder report | evidence manifest generation | BUILDER EVIDENCE ONLY |
| RC1 verification expansion | existing mutation suites plus focused RC1 tests | 5 RC1 focused tests; broader property/fuzz/concurrency corpus pending | PARTIAL |

RC1 does not change the independent-audit status. Phase 3A and Phase 3B remain `NOT_READY` until Gate 0 and the required independent evidence are closed.

## Phase 3B productization status

The synthetic Retail product workflow is evaluated separately from infrastructure audit status. Its product-review candidate status is recorded in `V3/PHASE_3B_PRODUCTIZATION_BUILD_REPORT.md`; it does not promote Phase 3A infrastructure or Phase 2C independent status.

| Phase 3B product group | Implementation | Verification | Status |
|---|---|---|---|
| P3B-WORK / PROFILE | `retail_product.py`, `project.yaml` examples | workspace validation and hash tests | COVERED |
| P3B-JOURNEY | `JOURNEY_TEMPLATES` and CLI `journeys` | template/output tests | COVERED |
| P3B-ACT | `assess_workspace`, activation engine integration | four strategy direction tests | COVERED |
| P3B-CAP / PROTO | capability state inventory and protocol profile reporting | assess/example smoke | COVERED |
| P3B-SIM | named simulation presets over Retail reference environment | preset smoke and lost-response test | COVERED |
| P3B-CLI | `agentnative retail init/validate/assess/journeys/recommend/simulate/blueprint/evidence` | installed-wheel workflow | COVERED |
| P3B-REP / ROADMAP | blueprint, evidence bundle, adaptive roadmap | blueprint/evidence reproducibility test | COVERED |
| P3B-TEST | product tests, inherited regressions/mutations, CI smoke | 25 focused; 142 pytest; 105 unittest | COVERED FOR SYNTHETIC PRODUCT REVIEW |

## Phase 3B closure remediation snapshot

| BRD requirement | Code / artifact | Test / evidence | Status |
|---|---|---|---|
| P3B-REM-SCHEMA-001..006 | `retail_schema.py`, `retail_workspace.schema.json`, `migrate_workspace`, `retail init --force` | `test_closure_remediation.py` schema/init cases; validator contract | BUILDER_VERIFIED |
| P3B-REM-EVID-001..005 | `_gate_recommendation`, `_protocol_readiness`, evidence-bound capability inventory, SecretDetector boundary | reference direction, protocol mismatch, secret regression suites | BUILDER_VERIFIED |
| P3B-REM-REC-001..006 | journey template prerequisites, reason codes, policy enforcement, conservative downgrade | exact scenario/reference tests and assessment sensitivity cases | BUILDER_VERIFIED |
| P3B-REM-SIM-001..009 | `SCENARIO_REGISTRY`, faithful delegation/malformed/outage/lost-response flows | one contract assertion per registered scenario | BUILDER_VERIFIED |
| P3B-REM-STORE-001..003 | SQLite schema v2, `retail_entities`, forward-only version guard | restart reload and schema checks | BUILDER_VERIFIED |
| P3B-REM-TXN-001..005 | `commit_order`, `commit_refund`, conditional transitions, reconciliation records | atomic inventory/refund/cancellation tests | BUILDER_VERIFIED |
| P3B-REM-CONC-001..004 | SQLite write serialization and conditional state transitions | concurrent last-item and inherited idempotency suites | BUILDER_VERIFIED |
| P3B-REM-RECOV-001..003 | durable payment/return/refund state and reconciliation APIs | restart/refund/payment evidence cases | BUILDER_VERIFIED |
| P3B-REM-CLI-001..004 / ART-001..003 | structured CLI errors, atomic writes, registry help, wheel smoke, canonicalization version | negative CLI and clean wheel-only script | BUILDER_VERIFIED |
| P3B-REM-PROV-001..005 | two-commit fields, CI metadata, artifact SHA-256, verifier, builder-only status | `run_phase3_rc1_evidence.py`, `verify_phase3b_evidence.py` | BUILDER_VERIFIED / CI RUN REQUIRED |
| P3B-REM-STATUS-001..004 | closure report and two independent handoff packages | status reconciliation review | READY_FOR_INDEPENDENT_REVIEW |

The status vocabulary is scoped: `BUILDER_VERIFIED` means local builder checks passed; `READY_FOR_INDEPENDENT_REVIEW` means the handoff is reproducible; `INDEPENDENTLY_VERIFIED` and `PRODUCTION_READY` are not claimed. Phase 2C remains independently `PHASE_2C_NOT_READY`.

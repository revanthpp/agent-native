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
| Phase 3B exit gate | synthetic reference only | Phase 3A + Phase 2C gates block | PHASE_3B_NOT_READY |

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

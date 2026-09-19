# Requirements Traceability

This first implementation maps the authoritative BRD to the smallest v0.1 vertical slice. Deferred requirements remain visible instead of being implied as complete.

| BRD requirement | Implementation | Tests / evals | Status |
|---|---|---|---|
| FR-DISC-001, FR-DISC-002 | `security.policy`, `acquisition.fetcher`, `discovery.discover` | URL policy and local fixture integration tests | Implemented in passive core |
| FR-DISC-003 | Local file and directory discovery | local fixture integration tests | Implemented |
| FR-DISC-004, FR-DISC-005 | Artifact hashes, timestamps, source URIs, normalized evidence | evidence traceability tests | Implemented |
| FR-CAP-001, FR-CAP-002 | OpenAPI normalization into `Operation` | parser and check tests | Implemented for JSON OpenAPI |
| FR-CAP-003, FR-CAP-004 | AR-012 through AR-017 deterministic checks | fixture suite | Implemented as passive observations |
| FR-PROT-001 | JSON OpenAPI structural parser | malformed OpenAPI tests | Implemented |
| FR-PROT-002, FR-PROT-003 | Adapter seams only; MCP/A2A adapters deferred | deferred eval manifest | Deferred |
| FR-ID-001 | AR-008 authentication declaration check | API fixture tests | Implemented |
| FR-ID-003, FR-ID-004, FR-ID-005, FR-ID-006 | passive scope observations only | deferred active evals | Deferred to verified-owner phase |
| FR-TXN-001 | AR-011 side-effect classification | mutation fixtures | Implemented conservatively |
| FR-TXN-002, FR-TXN-006 | AR-012, AR-013 passive evidence checks | agent-native and unsafe fixtures | Implemented as observation, no execution |
| FR-TXN-003, FR-TXN-004, FR-TXN-005 | AR-014 through AR-017 static signals | deferred simulator evals | Partially implemented |
| FR-REP-001, FR-REP-002 | terminal, Markdown, JSON renderers | report parity tests | Implemented |
| FR-REP-003, FR-REP-004, FR-REP-005 | scan diff, suggestions, signed bundles | deferred | Deferred |
| Security: SSRF / redirects / resource bounds | `NetworkPolicy`, manual HTTP client, bounded request loop | security tests | Implemented for v0.1 CLI |
| Evaluation strategy | `tests/`, `evals/`, catalog, thresholds, fixtures | deterministic unittest suite | Initial suite implemented |

## Remediation traceability

| QA finding | BRD / control intent | Root-cause change | Regression / evaluation | Release implication |
|---|---|---|---|---|
| P0-A public report secret leakage | FR-REP-001, FR-REP-002; public reports must be safe to share | Internal `Artifact` is projected to sanitized `ArtifactSummary`; raw content and headers are not public fields | `tests/security/test_remediation_regressions.py`, `tests/security/test_report_integrity.py`, `ADR-008` | Gate closed for this defect |
| P0-B `file://` bypass | FR-DISC-001; bounded acquisition and trust-boundary separation | `SafeFetcher` accepts only HTTP(S); `FixtureFetcher` handles explicit local fixtures | `tests/security/test_remediation_regressions.py`, `tests/security/test_network_boundaries.py` | Gate closed for this defect |
| P0-C incorrect evidence provenance | FR-DISC-004, FR-DISC-005; evidence must identify source artifact | Evidence carries `artifact_id`; validator verifies URI, type, and hash | provenance regression and tamper-rejection tests | Gate closed for this defect |
| P0-D mutation downgrade | FR-TXN-001, FR-TXN-006; conservative side-effect semantics | Structural method/path classification is monotonic and contradictory declarations warn | mutation regression plus check matrix | Gate closed for this defect |
| P0-E exit semantics | FR-REP-001; automation must observe blocked/incomplete scans | `ExecutionStatus` maps policy/acquisition/internal failures to nonzero CLI codes | CLI regression | Gate closed for this defect |
| P1-A malformed artifact invisibility | FR-DISC-004; advertised artifacts and limitations remain observable | Artifact inventory retains `PARSE_ERROR` and bounded error | malformed OpenAPI regression and report-integrity test | Gate closed for this defect |
| P1-B thin security/eval suite | NFR-SEC and evaluation strategy | deterministic network-boundary cases and a positive/negative/missing-evidence matrix for AR-001..AR-020 | `tests/security/test_network_boundaries.py`, `tests/evals/test_check_matrix.py`, `evals/corpus/check_matrix.json` | Improved; fuzzing and protocol conformance remain open |
| P2 missing license | Release hygiene / OSS distribution | Added Apache 2.0 license text | repository artifact inspection | Gate closed for this defect |

# Agent Native v0.1 QA Remediation

## Scope and method

The remediation sprint began by adding regression cases for each reported QA
finding and running them against the first implementation. The initial run
reproduced six failures: raw secret-bearing content in public JSON, `file://`
local-file access, incorrect OpenAPI evidence attribution, unsafe mutation
downgrade, zero exit status for blocked scans, and invisible malformed advertised
artifacts. Production changes were made only after those failures were captured.

## Finding disposition

| Finding | Defect class revealed | Root cause | Remediation | Regression coverage | Status |
|---|---|---|---|---|---|
| P0-A public report secret leakage | Data-boundary failure | Internal `Artifact` was serialized directly | Added `ArtifactSummary` and `PublicReport`; raw content/headers stay internal; evidence fragments are redacted | `test_public_json_never_contains_raw_secret_bearing_artifact`, `test_public_projection_excludes_artifact_payload_and_headers` | FIXED |
| P0-B `file://` trust-boundary bypass | Confused-deputy / input-validation failure | A generic fetcher treated local paths and network targets as one acquisition mode | `SafeFetcher` is network-only; local fixtures use separate `FixtureFetcher`; unsupported schemes are policy-blocked | `test_file_scheme_is_rejected_without_reading`, network policy tests | FIXED |
| P0-C wrong evidence source | Provenance integrity failure | Evaluators fell back to the first artifact when a relevant source was unavailable | Evidence sources are selected by artifact URI and operation source; validator checks ID, URI, type, and hash | `test_openapi_evidence_cites_openapi_artifact`, evidence-tamper test | FIXED |
| P0-D mutation side-effect downgrade | Semantic integrity / fail-open classification | Declarative metadata could override structural method semantics | `OperationRisk` keeps structural classification, detects contradiction, and applies monotonic mutation rules | `test_delete_cannot_downgrade_to_safe`, check matrix | FIXED |
| P0-E CLI exit semantics | Operational observability failure | Report rendering and execution status were not connected to process exit status | Added `ExecutionStatus` and nonzero codes for policy, acquisition, and internal failures | `test_invalid_scan_has_nonzero_cli_exit` | FIXED |
| P1-A malformed advertised artifact | Partial-failure observability failure | Discovery dropped parse failures from the artifact inventory | Artifact remains present with `PARSE_ERROR` and a bounded error; limitations preserve the reason | `test_malformed_advertised_openapi_remains_visible`, report-integrity test | FIXED |
| P1-B security/evaluation depth | Test-boundary weakness | Initial suite covered happy paths and a small SSRF sample | Added deterministic network-boundary, provenance, public-schema, control-sequence, and check-matrix tests | `tests/security/`, `tests/evals/test_check_matrix.py` | IMPROVED; broader fuzzing remains deferred |
| P2 missing license | Release hygiene failure | Repository metadata named a license without shipping its text | Added canonical Apache 2.0 `LICENSE` | repository inspection | FIXED |

## Architectural prevention

The recurring defect classes are prevented by four explicit seams:

1. Internal artifact content and public report data are different types.
2. Network acquisition and local fixture acquisition are different fetchers.
3. Evidence is a validated reference to an artifact, not an unverified text
   snippet.
4. Structural operation semantics are classified before advisory declarations;
   contradictory metadata can warn or escalate, but cannot make a destructive
   method safe.

## Residual risk

The remediation does not complete YAML OpenAPI parsing, safe `$ref` resolution,
MCP/A2A conformance, hosted egress isolation, ownership verification, active
verified-owner testing, or fuzzing/property-based parser coverage. Those remain
release gates for a broader deployment profile.

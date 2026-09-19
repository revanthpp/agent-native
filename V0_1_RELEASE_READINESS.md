# v0.1 Release Readiness

## Current recommendation

**V0.1 NOT RELEASE READY.** The remediation sprint closes the reported P0/P1/P2 defects and strengthens the local release candidate, but the full BRD release gates are not yet satisfied.

## Implemented in this slice

- Python-first package and CLI commands for version, check catalog, local fixture scans, JSON, Markdown, and terminal reports.
- Safe passive acquisition policy with HTTPS default, credential rejection, DNS/IP checks, manual redirect validation, request and response budgets, and timeouts.
- HTML structured metadata parsing and JSON OpenAPI normalization.
- Twenty stable AR-001 through AR-020 deterministic checks.
- Evidence objects with source URI, hash, timestamp, bounded redacted fragments, and confidence.
- Sanitized public report projection; raw artifact payloads and response headers are not serialized.
- Separate network and local-fixture acquisition paths; `file://` is policy-blocked.
- Evidence provenance validation across artifact ID, URI, type, and content hash.
- Conservative mutation classification with contradiction detection and execution-status-aware CLI exits.
- Artifact parse/acquisition failure observability and Apache 2.0 license.
- Traditional, API-enabled, and agent-native reference businesses.
- Threat model, ADRs, traceability, evaluation strategy, thresholds, known limitations, governance, and CI workflow.

## Verification run

The deterministic suite passes 33 tests across unit, integration, security, report-integrity, check-matrix, and reference-corpus evaluation layers. `compileall` also passes for `src`, `tests`, and `evals`.

The remediation regression suite initially reproduced six defects before the fixes. The current regression suite passes those six cases plus a completed-scan/zero-exit case. The expanded security suite covers redirect revalidation, DNS rebinding, private and mapped IPv6 targets, loopback policy, response bounds, timeout handling, and redirect budgets.

## Remaining blockers

- YAML OpenAPI support and safe `$ref` handling.
- MCP and A2A adapter/conformance suites.
- Full ambiguous fixture coverage for every check and deeper per-check semantic assertions.
- Hosted deployment egress isolation, abuse controls, and worker/resource quotas.
- Active verified-owner simulator, which is intentionally outside anonymous v0.1 scans.
- Fuzzing/property tests, dependency/SBOM review, and broader parser robustness corpus.
- CLI/Markdown/JSON snapshot parity at release scale.

The next implementation increment should complete YAML OpenAPI plus safe `$ref` coverage and add the protocol-specific MCP/A2A conformance suites before a release-ready claim.

## Remediation links

- [QA remediation](docs/remediation/V0_1_QA_REMEDIATION.md)
- [Public report boundary ADR](docs/adr/ADR-008-public-report-boundary.md)
- [Check coverage matrix](evals/corpus/check_matrix.json)

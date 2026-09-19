# Check Catalog

The BRD's suggested AR-001 through AR-020 IDs are retained as the stable v0.1 catalog. These are passive observations, not certification controls.

| ID range | Domains | Evidence rule |
|---|---|---|
| AR-001 to AR-004 | identity, security, discovery, interoperability | target URL, acquisition outcome, artifact metadata |
| AR-005 to AR-007 | capability semantics | normalized operations and schemas |
| AR-008 to AR-010 | authentication and delegated authorization | declared schemes/scopes only; no credential collection |
| AR-011 to AR-015 | transaction safety and recovery | method/path/extensions plus explicit metadata |
| AR-016 to AR-018 | reliability and provenance | public guidance, error responses, correlation markers |
| AR-019 to AR-020 | governance and secret handling | support markers and redacted artifact scan |

Each check definition in `src/agentnative/checks/catalog.py` includes ID, domain, version, severity, rationale, evaluation method, remediation, passive/active boundary, and confidence method.

## Fixture coverage

`evals/corpus/check_matrix.json` is the coverage manifest for all twenty checks,
and `evals/corpus/semantic_matrix.json` contains explicit fixture/check/status
assertions for the reference progression and credential corpus.
Each check has a positive fixture, a negative fixture, and a missing-evidence
fixture. The matrix test verifies that every catalog ID is represented, every
fixture exists, and each distinct fixture produces results without a check-level
error. The semantic matrix additionally asserts `actual.status ==
expected_status`; status expectations remain check-specific and are not
collapsed into a global score.

Security and reporting controls have additional focused cases for secret
redaction, public-schema exclusion, evidence tampering, terminal control
sequences, redirect validation, DNS rebinding, mapped IPv6, response limits,
timeouts, and execution exit status.

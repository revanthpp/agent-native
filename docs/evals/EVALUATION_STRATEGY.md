# Evaluation Strategy

The evaluation model keeps three questions separate:

1. Does Agent Native measure controlled fixtures correctly?
2. What readiness evidence is observable on the target?
3. Does Agent Native remain safe and bounded under hostile input?

## Initial suites

- `tests/unit`: models, redaction, HTML/OpenAPI parsing, individual checks.
- `tests/integration`: fixture discovery, scan-to-report flow, renderer parity.
- `tests/security`: URL/IP policy, redirects, response limits, secret handling.
- `tests/evals`: reference-business expected states and deterministic repeatability.

Every deterministic check should have positive, negative, and ambiguous/unknown coverage. The initial fixture suite exercises representative combinations; the full 20-case corpus is the next build increment.

## Reproducibility

Reports contain timestamps and UUID scan IDs for operational identity. Semantic snapshots must remove those fields before comparison. Check IDs, statuses, explanations, evidence source URIs, and normalized observations must remain stable for static fixtures.

## Failure isolation

Acquisition and check failures become bounded report limitations or `ERROR` results. They must not be converted into PASS and must not crash the CLI with a raw traceback in ordinary mode.

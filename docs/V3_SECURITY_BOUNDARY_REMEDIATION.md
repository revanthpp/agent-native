# v3 Security Boundary Remediation

## Current defect pattern

Independent QA found that sensitive-data handling was distributed across
multiple code paths. AR-020 had one pattern list, redaction had another, URI
sanitization had a third behavior, and report fields such as limitations and
evidence source URIs could bypass those controls. The result was detector and
reporting disagreement: a scan could identify a value in one path while a
different emitted surface still carried it raw.

## Root cause

Sensitive-data detection and sanitization were distributed across multiple
independent code paths, allowing detector/reporting disagreement and missed
output surfaces.

## Target architecture

```text
Raw scan state
    -> canonical SecretDetector
    -> Sanitizer and URI sanitizer
    -> SafeReportBuilder
    -> final output detector firewall
    -> JSON / Markdown / terminal
```

`SecretDetector` is the single definition of obvious credential-like material.
`Sanitizer` consumes it for text, nested structures, and URIs. `SafeReportBuilder`
converts the internal `ScanReport` into a public-only `PublicReport`. Renderers
accept the internal report only as an input to that mandatory conversion; they
render the safe model. `validate_output` scans the final serialized output and
fails closed without echoing matched content.

Limitations are structured as `Limitation(code, resource, reason)` and are
sanitized as part of the safe report conversion. The legacy `redaction` module
is now only a compatibility import surface; it contains no independent pattern
list.

## Invariants

- A sensitive value found by the detector cannot remain raw in a sanitized
  string, nested mapping/list, URI, evidence field, limitation, or emitted
  report.
- AR-020 and redaction use the same `SecretDetector` rules.
- Renderers do not receive raw `Artifact` objects or raw artifact content.
- Final output validation blocks detected sensitive material and its error does
  not include the value.
- Intentional SHA-256 `content_hash` fields are allowed by explicit context;
  standalone pure-hex values remain detectable.
- Harmless keyword-only language such as “token budgeting” does not fail AR-020.

## Affected modules

- `security/secrets.py`: canonical detection model.
- `security/sanitize.py`: text, nested-value, URI, and terminal sanitization.
- `reporting/safe.py`: safe report construction.
- `reporting/output.py`: final fail-closed firewall.
- `reporting/render.py`: safe-model-only rendering.
- `models.py`, `discovery.py`, `scanner.py`, and `checks/engine.py`: structured
  limitations, safe evidence, and canonical AR-020 integration.

## Migration plan

1. Preserve the existing CLI and report concepts while adding an explicit safe
   projection.
2. Route all existing redaction imports through the canonical sanitizer.
3. Convert production limitation construction to structured values.
4. Add semantic credential fixtures and cross-renderer invariant tests.
5. Add package identity and clean-wheel QA gates.

## Testing strategy

- Known regressions for limitation, source URI, AR-020, and report-boundary
  leaks.
- Invariant tests for detector/sanitizer agreement, safe-model separation, and
  final firewall failure behavior.
- Deterministic generated variants across key names, separators, case, and
  quoting.
- Semantic check matrix assertions with explicit expected statuses.
- Compile, dependency, package-build, and installed-CLI smoke checks.

## Explicitly deferred

Heuristic detection cannot guarantee discovery of every secret format or
encoding. YAML OpenAPI and safe `$ref` handling, MCP/A2A conformance, hosted
egress isolation, ownership verification, active testing, fuzzing beyond the
deterministic generated matrix, and dependency/SBOM policy remain outside this
hardening increment.


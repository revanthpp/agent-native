# Agent Native v0.1 Architecture

## Outcome

The v0.1 core turns a target into a bounded set of artifacts, normalizes supported evidence, runs deterministic checks, and renders the same result model as terminal, Markdown, or JSON output.

```text
target
  -> NetworkPolicy / SafeFetcher
  -> Artifact discovery
  -> HTML + JSON OpenAPI parsers
  -> normalized DiscoveredSurface
  -> 20 deterministic checks
  -> Evidence objects
  -> internal ScanReport
  -> sanitized PublicReport projection
  -> terminal / Markdown / JSON
```

## Boundaries

- `security`: URL and IP policy; never trusts target content as instructions.
- `acquisition`: bounded GET-only acquisition with manual redirects and response limits.
- `discovery`: minimal root plus common machine-artifact discovery; no arbitrary crawl.
- `parsers`: pure extraction; parsers never execute scripts or evaluate code.
- `models`: typed internal representation and serialized report shape.
- `checks`: independent deterministic evaluators with stable IDs and isolated failure handling.
- `reporting`: presentation only; it does not change evaluation semantics.

## Data boundary

The internal `Artifact` retains content for parsing and deterministic checks. It
never becomes the public report schema. `ScanReport.public_projection()` converts
each artifact to an `ArtifactSummary` containing identity, URI, media type, byte
size, hash, acquisition status, parse status, and a sanitized error. Public JSON,
Markdown, and terminal output are rendered only after evidence validation; raw
artifact content and response headers are not serialized.

Evidence is referential rather than copied: every finding points to an
`artifact_id`, source URI, artifact type, and content hash. The renderer rejects
unknown artifacts, URI/hash/type mismatches, and duplicate evidence IDs.

The normalized operation model is an internal compiler representation, not a new external protocol. OpenAPI is the first concrete adapter. MCP and A2A remain explicit future adapter seams.

## Security invariants

1. Network scans use HTTPS by default and reject embedded URL credentials.
2. Every host resolution is checked against private, loopback, link-local, multicast, reserved, and unspecified ranges.
3. Redirect destinations are revalidated and bounded.
4. Target content is data only; no JavaScript, shell, template, YAML execution, or arbitrary evaluator code runs.
5. Findings use `NOT_OBSERVED` when passive evidence is insufficient.
6. Evidence fragments are redacted before report serialization.
7. Local fixture acquisition is a separate `FixtureFetcher`; a `file://` URL is
   rejected by the production network fetcher and cannot select a local path.
8. Mutation classification is monotonic: structural DELETE or destructive
   language cannot be downgraded by a contradictory `x-side-effect: NONE` claim.

## Deliberate v0.1 tradeoffs

The first slice is standard-library-only and offline-friendly. JSON OpenAPI is supported deterministically; YAML, MCP conformance, A2A conformance, ownership verification, active staging tests, and hosted orchestration are deferred rather than represented as partially trusted behavior.

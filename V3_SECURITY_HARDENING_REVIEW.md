# Agent Native v3 Security Hardening Review

## Architecture changes

- Added one canonical `SecretDetector` for bearer credentials, API keys,
  tokens, access tokens, secrets, client secrets, passwords, session values,
  cookies, provider keys, and long encoded values.
- Added one `Sanitizer` for text, nested structures, lists, URI query values,
  URL credentials, and terminal control sequences.
- Added `SafeReportBuilder`; renderers now render `PublicReport`, not raw
  artifacts or internal scan state.
- Added a final `validate_output` firewall that fails closed without including
  sensitive values in its exception text.
- Replaced production free-form limitations with structured `Limitation`
  records and sanitized them at the safe-report boundary.
- AR-020 now calls the same detector used by sanitization and output validation.
- Added semantic fixture assertions, credential variants, cross-renderer tests,
  a workspace identity gate, and clean-install CI steps.

## Root causes eliminated

| QA defect | Architectural fix |
|---|---|
| Secret-bearing limitations | Structured limitations plus mandatory safe-report sanitization |
| Unsanitized Markdown source URIs | URI sanitizer is applied in `SafeReportBuilder`; Markdown only sees `PublicReport` |
| AR-020 misses bearer/token/session/cookie forms | Canonical detector with structured credential rules |
| Redaction and AR-020 disagree | Both consume `SecretDetector` |
| Structural matrix did not assert semantics | `semantic_matrix.json` and expected-status tests |
| Weak packaging validation | Build/install/smoke workflow plus local package verification |
| QA could target the wrong repository | `scripts/qa_identity.py` gate |

## Invariants and enforcing tests

| Invariant | Enforcement |
|---|---|
| INV-SEC-001: no detected secret in emitted formats | `test_no_detected_secret_reaches_any_renderer` |
| INV-SEC-002: AR-020 and sanitizer share semantics | `test_ar020_semantic_credential_matrix`, canonical detector tests |
| INV-SEC-003: external URIs are sanitized | `test_structured_limitations_and_evidence_source_uris_are_safe` |
| INV-SEC-004: renderers consume safe data | `SafeReportBuilder` and final report integrity tests |
| INV-SEC-005: firewall fails closed | `test_final_output_firewall_fails_closed_without_echoing_secret`, direct validator test |
| INV-SEC-006: limitations cannot leak secrets | structured limitation cross-renderer test |
| harmless keyword text remains safe | `test_safe_keyword_language_does_not_fail_ar020` |

## Tests

Executed successfully:

```text
PYTHONPATH=src:. python -m unittest discover -s tests -v
45 tests passed

PYTHONPATH=src python -m compileall -q src tests evals
passed

PYTHONPATH=src:. python scripts/qa_identity.py
QA_REPOSITORY_IDENTITY_CONFIRMED: Agent Native

python -m pip check
No broken requirements found
```

The test suite includes the existing unit, integration, SSRF, provenance,
mutation, parse-observability, semantic-matrix, and report-integrity tests.

## Adversarial results

Covered fake/nonfunctional values through artifact content, evidence fragments,
evidence source URIs, limitation resources/reasons, nested mappings/lists,
query parameters, credentialed URLs, JSON-like text, YAML-like text, HTML,
header syntax, mixed case, whitespace, colon/equal separators, and multiline
rendered output. All three report formats exclude the raw values. The detector
also avoids failing ordinary “token budgeting” language.

## Packaging validation

`python -m build --wheel --no-isolation` passed and produced
`dist/agentnative-0.1.0-py3-none-any.whl`. That wheel installed successfully
with `--no-index` into a clean virtual environment. `pip check`, `agentnative
--help`, a clean fixture scan, and a credential-fixture scan all passed outside
the source checkout; the credential scan returned `AR-020 = FAIL` as expected.
CI also installs the standard `build` frontend, builds the package, installs the
wheel into a clean virtual environment, and runs the same smoke scans.

## Known limitations

Secret detection is heuristic and focuses on obvious structured credential
forms. It cannot guarantee detection of every proprietary token format,
encoding, or deliberately disguised value. Report validation is defense in
depth, not a guarantee of perfect secret discovery.

## Architecture review answers

1. Renderers directly access raw scan artifacts: **No.** Rendering uses the
   `PublicReport` returned by `SafeReportBuilder`; artifact content and headers
   are not fields on that model.
2. AR-020 can disagree with the sanitizer: **No for the covered detector
   semantics.** Both use the same `SecretDetector` model and canonical rules.
3. Raw external URLs can enter limitation strings: **No in production paths.**
   Production limitations are structured, and the safe builder sanitizes every
   resource and reason. A legacy free-form value is treated as an unstructured
   limitation and sanitized before output.
4. A sanitizer miss can leave normal output: **The final output validator
   blocks detected residual sensitive content.** It is defense in depth, not a
   substitute for complete detection.
5. Validation errors can echo a secret: **No.** `UnsafeReportError` contains
   only a fixed generic message.

## Deferred work

YAML OpenAPI and safe `$ref` handling, MCP/A2A conformance, hosted egress
isolation, ownership verification, active verified-owner tests, broader fuzzing,
and dependency/SBOM policy remain deferred.

## v3.1 canonicalization follow-up

The v3.1 increment adds `SecretCanonicalizer`, which preserves the raw value
and produces at most two successive `urllib.parse.unquote` variants. The shared
variants are consumed by AR-020, text/URI sanitization, structured limitation
handling, and the final output firewall. This closes the encoded-assignment
class for path, fragment, key-only query, nested query-value, body, and bearer
representations without adding independent decoders.

The v3.1 regression set covers `token=FAKE`, `%3D`, `%3d`, double encoding,
the documented triple-encoding boundary, encoded bearer syntax, safe encoded
prose, canonicalization idempotence, bounded termination, and all three output
formats. The complete suite now passes **50 tests**.

The workspace has no Git metadata (`git rev-parse` reports
`NO_GIT_METADATA`); release handoff should capture a real commit SHA, tag, and
clean working-tree state before public distribution.

## Final recommendation

READY_FOR_INDEPENDENT_V3_QA

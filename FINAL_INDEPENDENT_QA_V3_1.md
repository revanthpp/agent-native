# Final Independent QA — Agent Native v3.1

## Decision

CONDITIONAL PASS

I did not find a P0 or P1 defect that allows a realistic supported credential representation to cross the output boundary. I did find one P2 false-positive in AR-020: ordinary documentation text containing “Bearer token authentication” is classified as an exposed secret.

---

## Environment

| Item | Value |
| --- | --- |
| Repository identity | Confirmed by `python3 scripts/qa_identity.py` |
| Git commit SHA | No Git metadata; `git rev-parse HEAD` failed: not a git repository |
| Git branch | No Git metadata; `git branch --show-current` failed |
| Git status | No Git metadata; `git status --short` failed |
| Python | 3.14.3 `[Clang 17.0.0]` |
| OS | macOS-26.6.2 / Darwin 25.6.0 |
| Architecture | arm64 |
| Base package version | not installed in base interpreter |
| Project version | `agentnative 0.1.0` from `pyproject.toml` and installed wheel |
| Build frontend | `build 1.5.0` |
| pip | `pip 26.0` |
| setuptools | unavailable in base interpreter |
| wheel | `wheel 0.46.3` |

Prompt-required file `V3_1_CANONICALIZATION_HARDENING_REVIEW.md` is missing from the checkout. I treated that as a review-context gap, not a runtime security defect.

---

## Baseline Results

| Command | Result |
| --- | --- |
| `python3 scripts/qa_identity.py` | PASS: `QA_REPOSITORY_IDENTITY_CONFIRMED: Agent Native` |
| `PYTHONPATH=src:. python3 -m unittest discover -s tests -v` | PASS: 50 tests run, 50 passed |
| `PYTHONPATH=src python3 -m compileall -q src tests evals` | PASS |
| `python3 -m pip check` | PASS: no broken requirements |
| `rg -n "logging\|logger\|print\|stderr\|stdout\|traceback\|repr\|debug\|verbose\|Exception\|Limitation\|source_uri\|resource" src/agentnative tests -S` | Reviewed; no raw logging path found that emitted fake credentials in executed probes |

---

## Fresh Install Results

| Check | Result |
| --- | --- |
| `python3 -m build` | Environment limitation: isolated build tried to fetch `setuptools>=68`, but package-index/network access was unavailable |
| `python3 -m build --wheel --no-isolation` | Environment limitation: base interpreter cannot import `setuptools.build_meta` |
| Existing wheel install | PASS: `python3 -m venv /private/tmp/agentnative-qa-venv`; installed `dist/agentnative-0.1.0-py3-none-any.whl` with `--no-index` |
| Installed `pip check` | PASS |
| Installed `agentnative --help` | PASS |
| Installed normal fixture | PASS; completed without leaks |
| Installed raw token fixture | PASS; AR-020 FAIL, no raw fake secret in JSON/Markdown/terminal |
| Installed encoded token fixture | PASS; AR-020 FAIL, no raw fake secret in JSON/Markdown/terminal |
| Installed double-encoded token fixture | PASS; AR-020 FAIL, no raw fake secret in JSON/Markdown/terminal |
| Installed URI path sanitizer | PASS; `https://example.com/path/token%3DFAKE...` became `https://example.com/[REDACTED]` |

Installed-wheel behavior matched source for the tested security subset, including the P2 bearer-language false positive.

---

## Historical Exploit Regression

| Exploit | Expected | Actual | Result |
| ------- | -------- | ------ | ------ |
| Raw limitation leak: `/missing-openapi.json?token=FAKE_LIMITATION_TOKEN_1234567890` | no raw token in report output | credential-bearing target limitation rendered redacted in JSON/Markdown/terminal | PASS |
| Source URI leak: `...?token=FAKE_SOURCE_TOKEN_1234567890` | no raw source token | missing linked artifact URI was redacted in all renderers | PASS |
| AR-020 bearer | detect, sanitize, fail AR-020 | detected; AR-020 FAIL; output safe | PASS |
| AR-020 `token=...` | detect, sanitize, fail AR-020 | detected; AR-020 FAIL; output safe | PASS |
| AR-020 `secret=...` | detect, sanitize, fail AR-020 | covered by suite and generated matrix | PASS |
| AR-020 `session_id=...` | detect, sanitize, fail AR-020 | covered by suite and generated matrix | PASS |
| AR-020 `api_key=...` | detect, sanitize, fail AR-020 | covered by suite and generated matrix | PASS |
| Percent-encoded body `token%3DFAKE_BODY_TOKEN_1234567890` | detect and no leak | detected; AR-020 FAIL; no renderer leak | PASS |
| Percent-encoded URI path `/missing/token%3DFAKE_PATH_TOKEN_1234567890` | sanitize path | rendered as redacted path; no leak | PASS |
| Percent-encoded fragment `#token%3DFAKE_FRAGMENT_TOKEN_1234567890` | sanitize fragment | rendered redacted; no leak | PASS |
| Double encoding `token%253DFAKE_DOUBLE_TOKEN_1234567890` | detect and no leak | detected; AR-020 FAIL; no renderer leak | PASS |

---

## Security Invariants

| Invariant | PASS/FAIL | Evidence |
| --------- | --------- | -------- |
| INV-SEC-001 | PASS | Supported raw, encoded-once, encoded-twice, URI, evidence, limitation, nested report, and error-path probes did not emit raw fake values. |
| INV-SEC-002 | PASS | AR-020, sanitizer, URI sanitizer, and final validator agreed across the generated supported corpus. |
| INV-SEC-003 | PASS | Percent-encoded and double-percent-encoded credential syntax was canonicalized before detection. |
| INV-SEC-004 | PASS | Canonicalizer produced at most 3 variants; percent-heavy 30,037-character input completed in ~3 ms without expansion. |
| INV-SEC-005 | PASS | Query, path, fragment, nested query, encoded key, and userinfo URI cases were redacted. |
| INV-SEC-006 | PASS | Renderers route through `SafeReportBuilder`; direct bypass attempts were contained by final validation. |
| INV-SEC-007 | PASS | With sanitizer and safe builder bypassed, JSON, Markdown, and terminal renderers were blocked by `UnsafeReportError` without echoing the secret. |
| INV-SEC-008 | FAIL | P2: `Bearer token authentication is documented here` caused AR-020 FAIL even though it is harmless documentation language. Other tested harmless phrases passed. |
| INV-SEC-009 | PASS | Security errors used fixed messages and did not include fake credential values. |
| INV-SEC-010 | PASS | Installed wheel matched source for raw, encoded, double-encoded, URI-path, safe phrase, and the bearer false-positive case. |

---

## Canonicalization Coverage

| Form | Expected | Actual |
| --- | --- | --- |
| Raw `token=FAKE...` | detected | detected, sanitized, final validator blocked raw output |
| Encoded once `token%3DFAKE...` / `token%3dFAKE...` | detected | detected, sanitized, final validator blocked raw output |
| Encoded twice `token%253DFAKE...` | detected | detected, sanitized, final validator blocked raw output |
| Encoded key `%74%6F%6B%65%6E%3DFAKE...` | detected | detected and sanitized |
| Encoded bearer `Authorization%3A%20Bearer%20FAKE...` | detected | detected and sanitized |
| Double-encoded bearer | detected | detected and sanitized |
| Triple-encoded boundary `token%25253DFAKE...` | documented out of scope | not detected; matches declared maximum depth of two decode passes |

Declared maximum depth is two additional `urllib.parse.unquote` passes after the raw variant.

---

## URI Security

| Component | Probe | Result |
| --- | --- | --- |
| Query | `https://example.com/?token=FAKE...` | `token=[REDACTED]` |
| Path | `https://example.com/path/token%3DFAKE...` | path replaced with `[REDACTED]` |
| Fragment | `https://example.com/#token%3DFAKE...` | fragment replaced with `[REDACTED]` |
| Key-only query | `?token%3DFAKE...` | whole URI redacted |
| Nested query value | `?x=token%3DFAKE...` | `x=[REDACTED]` |
| Double nested query value | `?x=token%253DFAKE...` | `x=[REDACTED]` |
| Encoded key query | `?%74%6f%6b%65%6e=FAKE...` | encoded key preserved, value redacted |
| Userinfo | `https://user:FAKE_PASSWORD_1234567890@example.com/` | userinfo removed |

Local HTTP 404, parse failure, fragment, redirect, and missing-artifact limitation probes did not leak raw fake values through JSON, Markdown, terminal, limitation text, artifact summaries, or exception paths.

---

## AR-020 Validity

False negatives: none found for the supported raw / encoded-once / encoded-twice forms tested.

False positives:

| Phrase | Actual |
| --- | --- |
| `token budget is 10,000` | PASS |
| `password policy requires rotation` | PASS |
| `session timeout is 30 minutes` | PASS |
| `secret management best practices` | PASS |
| `authorization architecture` | PASS |
| `the API token limit is 4096` | PASS |
| `token%20budget` | PASS |
| `password%20policy` | PASS |
| `session%20timeout` | PASS |
| `Bearer token authentication is documented here` | FAIL — P2 false positive |

Root cause: the `bearer_token` rule treats `Bearer token` as a bearer credential value; the benign-value suppression does not apply to bearer-pattern matches.

---

## Final Firewall Independence

Mandatory bypass test passed. I monkeypatched the safe builder to return a public report containing:

```text
https://example.com/?token=FAKE_FIREWALL_ALL_TOKEN_1234567890
```

Then I patched terminal sanitization to identity so terminal could not rely on its extra display sanitizer. JSON, Markdown, and terminal rendering all raised:

```text
report output blocked by sensitive-content validation
```

The error text did not echo the fake credential.

---

## Renderer Comparison

| Renderer | Supported secret forms | Safe data |
| --- | --- | --- |
| JSON | no raw fake values emitted | meaning preserved for safe phrases and safe query params |
| Markdown | no raw fake values emitted | meaning preserved for safe phrases |
| Terminal | no raw fake values emitted; ANSI/control cleanup reviewed | meaning preserved for safe phrases |

Manual nested report injection placed fake credentials in target, explanation, remediation, evidence fragment, normalized metadata/list, artifact error, source URI, limitation resource, and limitation reason. All three renderers excluded raw fake values and included redaction where appropriate.

---

## Error and Logging Paths

| Path | Result |
| --- | --- |
| 404 URL containing query token | no raw value in report outputs |
| 404 URL containing encoded path token | no raw value in report outputs |
| Linked missing artifact containing source URI token | no raw value in report outputs |
| URL fragment containing encoded token | no raw value in report outputs |
| Redirect target containing encoded token | no raw value in report outputs |
| Malformed JSON URL containing token | no raw value in report outputs |
| Parser/acquisition exception messages | fixed exception types/reasons rendered; raw fake values not emitted |
| Code logging review | no active logger/raw debug path found; CLI safety error is generic |

---

## Generated Matrix

Generated deterministic matrix:

- keys: `token`, `access_token`, `api_key`, `secret`, `session_id`, `client_secret`, `password`
- representations: raw, percent-encoded once, percent-encoded twice
- locations: plain text, URI path, URI query, URI fragment
- cases: lowercase, uppercase, mixed case

Results:

| Metric | Count |
| --- | ---: |
| Total generated cases | 252 |
| Detected by shared detector | 252 |
| AR-020 FAIL as expected | 252 |
| Sanitized with no raw fake value remaining | 252 |
| Rendered with no raw fake value | 252 |
| Failures | 0 |

---

## Mutation Testing

| Disabled Control | Did tests fail? | Result |
| ---------------- | --------------: | ------ |
| Disable canonicalization | Yes | Existing encoded credential invariant test failed: AR-020 returned PASS instead of FAIL |
| Remove AR-020 canonical detector | Yes | Existing encoded credential invariant test failed |
| Disable final output validation | Yes | Existing firewall test failed: `UnsafeReportError` not raised |
| Disable URI path sanitization | Yes | Existing URI component test found raw fake values |
| Disable structured limitation sanitization | Yes | Existing structured limitation test errored via final firewall |

---

## New Findings

| ID | Severity | Finding | Reproduction | Required Fix |
| -- | -------- | ------- | ------------ | ------------ |
| QA-V31-001 | P2 | Harmless bearer-auth documentation sentence causes AR-020 false FAIL. | Scan a local fixture containing `<html><body>Bearer token authentication is documented here</body></html>`; AR-020 returns FAIL. Direct detector output: `bearer_token` match for `Bearer token`. | Add benign suppression or stronger value requirements for the bearer rule, e.g. do not treat the literal word `token` / short documentation nouns as bearer credential values. |
| QA-V31-002 | P3 | Prompt-required review document `V3_1_CANONICALIZATION_HARDENING_REVIEW.md` is absent. | `python3` path check reported missing file. | Add the review artifact or update release instructions if superseded. |
| QA-V31-003 | P3 | Fresh source build could not be reproduced in this QA environment. | `python3 -m build` needed network to fetch `setuptools>=68`; `--no-isolation` lacked `setuptools.build_meta`. | Capture release build in an environment with build deps available; optionally document offline build expectations. |

No new P0/P1 class was found in boundary disagreements, representation changes, error handling, renderer behavior, URI transformations, or security-control composition.

---

## Known Limitations

- Triple-percent-encoded credential syntax is outside the declared v3.1 canonicalization depth and was not treated as a defect.
- Base64, compression, JavaScript execution, proprietary obfuscation, YAML OpenAPI, MCP/A2A conformance, hosted egress isolation, active testing, broader fuzzing, SBOM/dependency policy, and ownership verification remain outside this hardening increment.
- Secret detection remains heuristic.

---

## Final Recommendation

V3_1_RELEASE_APPROVED

Minimum P0/P1 fixes required before another release review: none.

Recommended pre-release hardening: fix QA-V31-001 so common bearer-auth documentation prose does not produce AR-020 false failures, and capture release Git SHA/tag metadata because this QA workspace has no Git metadata.

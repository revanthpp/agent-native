# v2 Threat Model

The canonical v2 implementation is under `src/agentnative/`; `V2/` contains
historical prompts and BRD inputs. This file records the active Phase 2A/2B
security boundary.

## Hostile protocol artifacts and parser exception leakage

Threat: a malformed or hostile protocol artifact, including an unsupported YAML
tag, causes a parser-specific exception to escape a public adapter operation.
That can leak implementation details, break callers, or create an unsafe
registry-only containment assumption.

| Control | Canonical evidence |
|---|---|
| Safe parser | `src/agentnative/protocols/openapi/parser.py` uses `yaml.safe_load` and normalizes `yaml.YAMLError`. |
| Adapter boundary | `src/agentnative/protocols/openapi/adapter.py` maps expected parser failures to `AdapterResult` status `INVALID` with `AdapterError` evidence. |
| Registry isolation | `src/agentnative/protocols/registry.py` performs a safe diagnostic pass and retains structured internal-error evidence for unexpected defects. |
| Direct-call regression | `tests/protocols/test_openapi_error_boundary.py` covers unsafe tags, malformed YAML, public operations, provenance, and direct-vs-registry consistency. |
| Mutation regression | `scripts/run_phase2b_mutations.py` includes `M-ADAPTER-YAML-ERROR`, which bypasses the production normalization seam and must be caught. |
| Residual risk | Independent re-audit is still required; the prior audit evidence remains unchanged and Phase 2C is not started. |

Defense in depth is therefore:

```text
safe parser + adapter-level normalization + registry isolation
```

Target-controlled content remains data. The structured error model exposes only
stable messages, safe metadata, artifact identity, source URI, content hash,
and acquisition provenance; it does not expose parser tracebacks or raw
artifact contents.

## Phase 2C transaction and evidence threats

| Threat | Preventive control | Detective control / test | Residual risk |
|---|---|---|---|
| cross-principal / cross-agent / cross-environment idempotency replay | canonical fingerprint binds business, environment, principal, agent/provider, capability, resource, amount/currency, payload, quote, and confirmation; atomic key claim | material-dimension conflict matrix, conflict hash evidence, receipt disclosure test, `M-IDEM-OMIT-*` mutations | process-local store is not crash-durable or distributed |
| duplicate transaction or retry replay | idempotency key is separate from a canonical logical transaction fingerprint; same-fingerprint callers single-flight and replay one receipt | response-loss, same-key concurrency, result-replay trace and receipt tests | adapter must honor the boundary in external deployments |
| confirmation replay or substitution | atomic confirmation binding maps confirmation to logical transaction ID and fingerprint; completed replay resolves before consumption | same-transaction expiry replay, distinct-key competition, confirmation race, `M-IDEM-CONFIRMATION-ORDER` and `M-CONFIRMATION-CROSS-TX-REUSE` mutations | human process outside the reference runner |
| quote tampering, expiry, or TOCTOU | quote binding and pre-commit version check | stale quote/resource-change tests | targets may expose incomplete version signals |
| partial success or failed compensation | first-class `PARTIAL`, bounded compensation path | partial/compensation tests and trace events | business-specific restoration semantics |
| hidden mutation | pre/post adapter snapshot and action-class comparison | critical hidden-mutation test | opaque external side effects require target evidence |
| forged or modified receipt | canonical JSON SHA-256 integrity | receipt modification verification tests | hash integrity is not signer identity |
| trace/receipt mismatch or telemetry leakage | shared root context and redacted events | cross-protocol and secret-redaction tests | downstream collectors may apply their own retention policy |
| simulator environment escape or excessive value | environment/action/value ceilings; production-active off | wrong-environment and ceiling tests | deployment configuration must preserve defaults |
| malformed value or currency bypass | exact bounded `MonetaryValue` parsing, required currency, exact ceiling matching, no FX conversion | monetary boundary matrix and `M2C-RISK-*` mutations | a future currency set expansion must preserve the same-match rule |
| concurrent duplicate commit | atomic pre-commit `PENDING` idempotency claim, same-hash wait/replay, different-hash conflict | bounded 8-worker test and `M2C-IDEMPOTENCY-ATOMIC-CLAIM` / `M2C-IDEMPOTENCY-HASH-CONFLICT` mutations | reference store is process-local and not crash-durable |
| dry-run side effects | separate non-mutating `build_plan()` boundary; active prepare/preview excluded; snapshot fail-closed check | hostile prepare/preview/plan tests and `M2C-DRYRUN-ACTIVE-PREVIEW` mutation | adapter construction must remain side-effect free outside the simulator |
| runaway retry / denial-of-wallet | bounded, classified, observable retries | retry mutation and failure-injection tests | external rate limits remain deployment-specific |

The Phase 2C implementation is intentionally synthetic and protocol-isolated;
it does not establish universal production safety or authorize arbitrary live
business execution.

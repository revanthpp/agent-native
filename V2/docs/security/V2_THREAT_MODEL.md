# v2 Threat Model — Phase 2A

| Threat | Preventive control | Detective control | Test | Residual risk |
|---|---|---|---|---|
| malicious YAML tags | `safe_load`; no object construction | parse error/limitation | safe parser test | dependency parser bugs |
| recursive/giant refs | depth/count bounds, cycle detection | explicit limitations | ref adversarial tests | CPU pressure below input cap |
| local/private ref escape | pure parser blocks file/remote resolution | limitation code | blocked ref tests | acquisition boundary must be separately tested |
| MCP tool poisoning | structural terms cannot be downgraded by prose | contradiction limitation | deceptive tool test | runtime behavior unknown in passive mode |
| A2A spoofed capability | compatibility does not establish trust | trust limitation | Agent Card test | identity gate is Phase 2B |
| adapter failure cascade | registry catches per-adapter failure | error result | isolation test | malformed adapter implementation still needs review |
| capability risk downgrade | monotonic graph merge | highest-risk result | normalization test | semantic equivalence remains conservative |
| secret leakage | no credentials or raw artifact bodies in results | typed output boundary | secret regression test | later report layer must retain redaction |

Active execution is not present in Phase 2A. Ownership, delegation, replay, policy, transaction, receipt, and telemetry controls are mandatory later gates.

## Phase 2B additions

| Threat | Preventive control | Detective control | Test/eval | Residual risk |
|---|---|---|---|---|
| ownership takeover / wrong host | exact hostname binding, challenge expiry, redirect host check | verification evidence/status | ownership adversarial tests | DNS/HTTPS trust still depends on external infrastructure |
| stolen or replayed delegation | expiry, revocation, principal/agent/provider/audience/resource checks | reason-coded denial | delegation denial tests | signature/token transport is Phase 2B follow-up |
| policy bypass / stale policy | deterministic ordered rules, secure default deny, version | matched rule and reason | policy repeatability/lint tests | policy cache invalidation is not yet implemented |
| cross-protocol identity confusion | identity remains separate from protocol compatibility | trust-boundary limitations | cross-protocol capability tests | protocol identity mapping remains conservative |

| DPoP proof replay or substitution | ES256 proof verification, method/URI/iat/jti/nonce/ath checks, replay store | explicit INVALID result and replay reason | canonical DPoP tests and mutation run | in-memory replay state is reference-only and must be externalized for distributed deployment |
| stale policy authorization | immutable version store and current-version lookup | audit record and explicit policy version | policy version tests | distributed cache invalidation is outside this reference implementation |

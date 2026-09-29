# Phase 3 Threat-Model Delta

Status: `BUILDER BASELINE — OPEN INDEPENDENT REVIEW`

| Threat | Preventive control | Detective control | Residual risk |
|---|---|---|---|
| Tampered pack | canonical content hash before compilation; optional signature policy | hash mismatch test | signing-key trust policy is environment-specific |
| Malicious/oversized manifest | safe YAML, depth/size/reference limits | resource-limit tests | fuzz duration and process isolation remain to be expanded |
| Cross-pack capability confusion | namespaced capability/evaluation IDs | graph isolation tests | shared-core contracts need more negative fixtures |
| Cross-tenant evidence reuse | tenant+pack scoped EvidenceStore | tenant isolation tests | persistent multi-tenant storage is not yet implemented |
| Stale/conflicting evidence | typed states and validity interval | conflict/stale tests | source authority ranking is not yet policy-configurable |
| Unsafe recommendation | deterministic rules, unknowns, `DO_NOT_ACTIVATE`, economics | counterfactual tests | benchmark corpus is still seed-sized |
| Protocol drift | version/source/hash ProtocolRegistry | A2A transition fixture | automated remote retrieval is intentionally absent |
| Transactional pack bypasses v2 | required core guarantee gate | default Retail constructor denial | Phase 2C independent gate remains open |
| Unknown commerce outcome | v2 idempotency record and singular receipt; explicit unknown state | lost-response/replay test | store is process-local and not crash-durable |
| Sandbox reaches production | Retail environment is synthetic and core-gated | endpoint/credential boundary still required for connector stage | generic connector binding is not yet implemented |
| Untrusted core evidence | subject-bound signed attestation, expiry, revocation, trusted key/environment policy | signature and revocation tests | independent auditor must issue the actual release attestation |
| Signed pack tampering | canonical semantic payload and dependency-lock hash | signature, key, and lock mismatch tests | key distribution/rotation operations remain deployment-owned |
| Crash after mutation | SQLite idempotency/order/receipt/reconciliation records; pending state blocks blind retry | restart replay and receipt verification tests | downstream reconciliation protocol is synthetic |
| Credential or endpoint confusion | credential references, endpoint allowlists, environment and side-effect policy | connector negative tests | DNS rebinding defense requires a real HTTP client boundary |
| Duplicate refund | distinct refund identity, payment authorization boundary, ceiling, receipt separation | refund replay/ceiling tests | payment-network behavior is simulated only |

## Out of scope

No real payment credentials, PHI, production endpoints, or commercial connector credentials are accepted by the Phase 3 reference environment.

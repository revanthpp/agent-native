# Agent Native Phase 3 Architecture

Status: `BUILDER BASELINE — NOT READY FOR INDEPENDENT REVIEW`

Phase 3 remains one horizontal control plane. Sector packs are declarative, namespaced inputs that compile into existing v2 capability and evaluation models. They do not replace identity, delegation, policy, transaction safety, receipts, evidence, or observability.

```text
Pack YAML
  → PackLoader
  → content hash / provenance / compatibility / resource limits
  → PackRegistry lifecycle + core guarantee gate
  → namespaced capability/evaluation compilation
  → typed EvidenceStore + ProtocolRegistry
  → ActivationStrategyEngine / MaturityFramework
  → CoreTrustStore / signed attestation verification
  → SQLiteStateStore (idempotency, orders, receipts, reconciliation, audit evidence)
  → ConnectorEnvironmentPolicy / SyntheticMerchantConnector
  → v2 TransactionSafetyEngine + ReceiptEngine + TraceRecorder
```

## Boundaries

| Boundary | Owner | Invariant |
|---|---|---|
| Pack source | pack | sector semantics only; no secrets or runtime mutation |
| Pack loader | core extension | malformed, oversized, incompatible, or tampered input fails closed |
| Pack registry | core extension | lifecycle and disablement are explicit and reversible |
| Core guarantee registry | v2 release evidence | transactional packs cannot activate without independent guarantees |
| Evidence store | shared v3 service | tenant/pack scope, provenance, freshness, conflict, and integrity are explicit |
| Protocol registry | shared v3 service | version/hash drift is visible; presence is not conformance |
| Retail environment | retail pack | deterministic state machine delegates transaction identity and receipts to v2; payment, return, and refund use separate identities |
| Durable reference state | RC1 reference backend | SQLite constraints and transactions preserve idempotency, order events, receipts, and reconciliation across restart |
| Connector boundary | shared RC1 service | tenant, environment, endpoint, credential reference, capability, and side-effect mode are explicit |

## Transactional activation gate

Retail requires the following independently verified guarantees before the reference environment can construct:

```text
identity_binding_v1
delegation_scope_v1
transaction_identity_v1
replay_safe_confirmation_v1
idempotency_atomicity_v1
receipt_integrity_v1
```

The current repository evidence is builder-remediated/pending independent Phase 2C re-audit, so the default gate rejects Retail activation. Tests may inject a clearly named synthetic `CoreGuaranteeRegistry.for_test()` fixture; that fixture is not release evidence.

## Retail reference journey

The reference environment supports stable product/variant discovery, quote creation with expiry and observed inventory, confirmation-bound checkout, idempotent order submission, lost-response simulation, cancellation, return eligibility, payment authorization simulation, return transitions, and refund ceilings/idempotency. Durable storage is opt-in for the reference backend; production adapters and real payment credentials remain out of scope. Unknown outcomes are represented explicitly and routed to reconciliation rather than blind retry.

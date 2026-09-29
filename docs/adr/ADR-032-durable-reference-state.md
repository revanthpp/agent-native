# ADR-032: SQLite durable reference state

Status: Accepted for RC1 implementation

RC1 adds a dependency-free SQLite reference store with schema version metadata, atomic idempotency claims, receipts, orders, append-only order events, confirmations, reconciliation work, pack state, evidence, and attestations. The business layer receives a store interface-compatible object and does not require a managed database.

Pending or ambiguous mutations are returned as reconciliation-required; restart recovery never blindly re-executes a downstream mutation.

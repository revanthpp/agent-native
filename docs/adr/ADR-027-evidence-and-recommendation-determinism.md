# ADR-027: Typed evidence and recommendation determinism

Status: accepted for Phase 3 builder implementation.

Activation inputs remain readable domain values, but evidence can carry source type, source reference, validity interval, confidence, environment, tenant, pack, collector, state, and hash. Unknown, stale, and conflicting observations are not silently favorable. Recommendations are generated from canonical inputs plus pack and engine versions; no composite score is emitted, and economics may produce `DO_NOT_ACTIVATE`.


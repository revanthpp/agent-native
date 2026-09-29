# ADR-026: Pack provenance, integrity, and core-gate inheritance

Status: accepted for Phase 3 builder implementation.

Pack content is hashed after removing non-semantic transport provenance fields. A declared hash must match the computed hash. Transactional packs declare required core guarantees. Activation requires a `CoreGuaranteeRegistry` whose entries are both verified and independently verified. The default registry is empty; test fixtures are explicitly named and never treated as release evidence.


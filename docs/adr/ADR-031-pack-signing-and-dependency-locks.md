# ADR-031: Signed pack payloads and dependency locks

Status: Accepted for RC1 implementation

Pack signatures cover a canonical semantic envelope rather than raw YAML bytes. The envelope binds pack identity, version, schema, content hash, core requirement, required guarantees, dependency-lock hash, and lifecycle timestamps. Environment-specific trust policy controls allowed algorithms, publishers, and key IDs.

The reference implementation uses maintained Ed25519 support from `cryptography`; private keys are supplied by callers and are never stored in the repository.

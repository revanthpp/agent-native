# ADR-028: Protocol versioning and drift management

Status: accepted for Phase 3 builder implementation.

Protocol profiles carry exact protocol/profile versions, `as_of`, source URL/hash, supported and unsupported features, extensions, and drift status. Comparing a candidate profile detects source/version changes and representative breaking changes such as removed required features or authentication support. A protocol label alone is never a conformance pass.


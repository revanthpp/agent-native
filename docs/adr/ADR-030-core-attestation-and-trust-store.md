# ADR-030: Subject-bound core attestations

Status: Accepted for RC1 implementation

Core guarantees are represented by a signed, time-bounded attestation bound to repository, commit, package version, and core content hash. A trust store verifies the Ed25519 signature, key lifecycle, environment, expiry, revocation, and evidence references before a registry can construct independently verified guarantees.

`CoreGuaranteeRegistry.for_test()` remains explicitly fixture-only. It is not a production trust root and must not be used by a signature-required registry or production connector path.

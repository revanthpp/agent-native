# ADR-017: Receipt Integrity

Status: Accepted

Receipts use a canonical JSON payload and SHA-256 integrity marker. Raw input
bodies and credentials are not stored. Verification detects modifications to
decision, amount, resource, policy, agent, trace, or request hash.

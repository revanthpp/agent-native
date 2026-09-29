# Receipt Retention

Receipt retention is configurable by deployment. The reference implementation
writes sanitized JSON only when the caller requests an output or local run
record. Receipts contain hashes and references rather than raw request bodies,
tokens, payment credentials, or unnecessary personal data.

Retention does not change integrity verification. Destroyed or expired receipt
data must be reported as unavailable evidence rather than reconstructed.

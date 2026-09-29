# ADR-020: Dry-Run Semantics

Status: Accepted

Dry-run performs identity, delegation, capability, risk, policy, and preview
evaluation but never calls state-changing execution. Outputs are explicit
`WOULD_ALLOW`, `WOULD_DENY`, or `WOULD_REQUIRE_HUMAN` results.

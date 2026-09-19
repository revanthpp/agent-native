# ADR 003 Passive Boundary

## Decision

Anonymous v0.1 scans perform bounded GET-only acquisition and static inspection. They never execute JavaScript, submit forms, authenticate, or invoke discovered business operations.

## Consequence

Runtime semantics are reported as `NOT_OBSERVED` or `WARN` when passive evidence cannot establish them. Verified staging simulation is a future phase.

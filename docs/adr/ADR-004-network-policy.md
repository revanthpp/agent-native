# ADR 004 Safe Network Acquisition

## Decision

Use a manual HTTP client with URL credential rejection, DNS/IP validation, manual redirects, request/redirect budgets, timeouts, and response byte limits.

## Consequence

The hosted service must add process/container egress isolation and resource quotas. The CLI can provide deterministic local file fixtures without network access.

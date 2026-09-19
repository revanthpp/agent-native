# ADR 001 Deterministic First

## Decision

Implement v0.1 checks with deterministic parsing and structural rules. Do not require an LLM for the core scan.

## Why

The BRD makes evidence, reproducibility, and security-critical decision independence from LLM output non-negotiable. Deterministic checks are easier to replay, audit, fuzz, and explain.

## Consequence

Some semantic ambiguity remains `WARN` or `NOT_OBSERVED` until a future non-authoritative semantic layer can abstain and preserve source evidence.

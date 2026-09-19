# ADR 006 Check Architecture

## Decision

Checks are cataloged metadata plus isolated evaluator functions over the normalized surface. A failing evaluator becomes an `ERROR` result and does not abort sibling checks.

## Consequence

The catalog is easy to test and extend, while a future plugin SDK must preserve the same evidence and security boundaries.

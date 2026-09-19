# ADR 007 Existing Protocol Adapters

## Decision

Use an internal normalized representation as a compiler intermediate model and adapt OpenAPI, MCP, A2A, and ordinary HTTP through modular adapters. Do not create a new public manifest or protocol.

## Consequence

Protocol support can evolve independently without changing the product's evidence model.

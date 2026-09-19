# ADR 005 Evidence Model

## Decision

Every actionable finding carries source URI, artifact type, acquisition timestamp, content hash, bounded redacted fragment, normalized representation, observation, and confidence.

## Consequence

Reports remain independently understandable while raw fetched bodies are not persisted by the v0.1 report layer.

# v2 Decision Log

| Decision | Rationale |
|---|---|
| Keep v2 isolated under `v2/` | BRD requires independent install/test/run and v1 preservation. |
| Pin MCP `2026-07-28` and A2A `1.0.0` | BRD requires explicit protocol versions; no silent latest behavior. |
| Parse protocol documents as data only | Phase 2A must not execute target-controlled descriptions, extensions, or tools. |
| Use conservative limitations for remote `$ref` | Network policy belongs at acquisition, not inside a pure parser. |

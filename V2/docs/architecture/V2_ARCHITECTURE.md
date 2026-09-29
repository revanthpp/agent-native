# v2 Architecture — Phase 2A baseline

```text
artifact -> adapter registry -> protocol adapter -> AdapterResult
                                      |                 |
                                      +--> Capability --+
                                                |
                                      CapabilityGraph
```

The future activation path is `agent -> identity -> delegation -> policy -> simulator/edge -> receipt + trace`. Phase 2A stops before any active execution.

Trust boundaries are: public target/artifact input; protocol parser; canonical graph; future verified-owner boundary; future policy boundary; and future receipt/evidence boundary. Target metadata is data only. Adapters never execute scripts, tools, prompts, extensions, or credentials.

Failures are isolated per adapter. A malformed MCP document yields a bounded MCP result and does not suppress OpenAPI or A2A results. Unsupported versions, extensions, remote refs, and lifecycle features become explicit limitations rather than PASS results.

`SafeRefResolver` supports bounded local JSON Pointer refs, detects cycles and missing refs, blocks `file:`/absolute refs, and refuses remote ref resolution until safe acquisition is explicitly wired. Capability merging retains the highest structural side-effect risk and all evidence references.

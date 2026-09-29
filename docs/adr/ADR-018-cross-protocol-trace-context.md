# ADR-018: Cross-Protocol Trace Context

Status: Accepted

A caller supplies one `TraceContext` to A2A, MCP, HTTP/OpenAPI, simulator, and
receipt boundaries. Structured events preserve one root `trace_id` and
`correlation_id`; the export includes an OpenTelemetry-compatible shape.

# Cross-Adapter Boundary Retest

## MCP

Malformed direct MCP inputs did not leak third-party/parser exceptions.

Observed:

- wrong top-level type: `NOT_DETECTED`;
- invalid `tools` inventory: `INVALID` with `MCP_TOOLS_INVALID`;
- malformed input/output schemas: `VALID_WITH_WARNINGS` with schema limitations;
- unknown extensions/nested unsupported data: `VALID_WITH_WARNINGS` with `MCP_UNKNOWN_EXTENSIONS`;
- malformed top-level `auth`: silently ignored.

Finding: `V2-FINAL-LOW-001`, non-blocking LOW. MCP should emit a limitation for malformed top-level auth fields.

## A2A

Malformed direct A2A inputs did not leak exceptions.

Observed:

- wrong top-level type: `NOT_DETECTED`;
- malformed/missing card fields: `INVALID`;
- malformed skills/auth are structured when the card reaches those checks;
- duplicate skill and malformed auth are covered by root tests.

No A2A release blocker found.

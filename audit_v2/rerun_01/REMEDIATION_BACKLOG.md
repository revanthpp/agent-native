# Remediation Backlog

No P0/P1 release blockers remain for Phase 2A or Phase 2B.

## V2-FINAL-LOW-001

Severity: LOW

MCP malformed top-level auth field is silently ignored.

Reproduction:

```python
MCPAdapter().parse({"tools": [{"name": "x"}], "auth": "bad"})
```

Expected:

- `MCP_INVALID_AUTH` limitation or structured target-input warning.

Actual:

- status `VALID`;
- no limitation;
- no auth requirement.

Recommended remediation:

- Add a limitation when `auth`, `authorization`, or `authentication` exists and is not an object.

Release impact:

- Non-blocking. No exception leak, unsafe execution, or Phase 2B fail-closed regression observed.

# Release Gate Matrix

| Gate | Result | Notes |
|---|---|---|
| Clean editable install | PASS | Required network approval for dependencies. |
| `pip check` | PASS | No broken requirements. |
| Root pytest | PASS | 77 passed, 144 subtests. |
| Root unittest | PASS | 77 tests OK. |
| Wheel build/install | PASS | Installed from local wheelhouse into second env. |
| CLI smoke | PASS | Required help commands passed. |
| Canonical root package | PASS | No production `v2core.py`; no `agentnative_v2`. |
| Adapter contract | PASS | Required methods present and exercised. |
| Extension SDK | PASS | Independent dummy adapter registered without built-in changes. |
| Same-origin remote refs | PASS | Independent nested same-origin/provenance checks passed. |
| Unsafe refs blocked | PASS | localhost/private/link-local/IPv6/file/ftp blocked before fetch. |
| Malicious YAML fail-closed | FAIL | Direct OpenAPI adapter leaks `ConstructorError`. |
| Policy linter | PASS | Independent trigger/safe cases passed. |
| Signature/replay | PASS | Independent checks passed. |
| Delegation confused deputy | PASS | Independent checks passed. |
| Mutation claim | PASS | 17/17 reproduced. |

Final gate: `PHASE_2A_CONDITIONALLY_READY`, `PHASE_2B_CONDITIONALLY_READY`, `PHASE_2C_NOT_STARTED`.

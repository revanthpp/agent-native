# Architecture Results

- Active branch: `develop/v2`.
- `v1.0.0` tag is present.
- Canonical production implementation is under `src/agentnative/`.
- No `src/agentnative/v2core.py` remains.
- No production `agentnative_v2` package was found.
- Wheel inspection found no `v2core` or `agentnative_v2` entries.
- `scripts/verify_package_contents.py audit_v2/wheelhouse/agentnative-2.0.0a1-py3-none-any.whl` returned `PACKAGE_CONTENT_VALID runtime_files=67`.

## One Obvious Module

- OpenAPI `$ref`: `src/agentnative/protocols/openapi/refs.py`, with parsing in `parser.py` and adapter wiring in `adapter.py`.
- MCP: `src/agentnative/protocols/mcp/adapter.py`.
- A2A: `src/agentnative/protocols/a2a/adapter.py`.
- Identity/signature/replay: `src/agentnative/identity/`.
- Delegation: `src/agentnative/delegation/`.
- Policy: `src/agentnative/policy/`.

Protocol logic no longer appears duplicated in a production `v2core.py`. Historical references remain in prompts/docs under `V2/`, which are not production code.

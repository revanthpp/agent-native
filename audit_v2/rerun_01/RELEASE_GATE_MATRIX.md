# Release Gate Matrix

| Gate | Result | Notes |
|---|---|---|
| Prior OpenAPI finding | PASS | Direct and registry hostile YAML return structured INVALID. |
| Public OpenAPI operations | PASS | detect/parse/validate/normalize/enumerators do not leak ConstructorError. |
| Internal error separation | PASS | RuntimeError remains distinguishable; registry marks ERROR. |
| CLI/report sanitization | PASS | No traceback/raw hostile payload; structured JSON remains useful. |
| MCP/A2A boundary | PASS with LOW finding | No exception leak; MCP malformed top-level auth silently ignored. |
| Adapter contract | PASS | Required methods present. |
| Extension adapter | PASS | Independent dummy adapter registers and isolates failure. |
| Remote `$ref` regression | PASS | Same-origin/provenance and redirect block verified. |
| Phase 2B spot checks | PASS | Identity, replay, delegation, policy, DPoP checks passed. |
| Clean env install | PASS | Needed network approval for dependencies. |
| `pip check` | PASS | No broken requirements. |
| Pytest | PASS | 84 passed, 158 subtests. |
| Unittest | PASS | 84 tests OK. |
| Wheel build/install | PASS | Built and installed from local wheelhouse. |
| Package contents | PASS | 67 runtime files; no `v2core`/`agentnative_v2`. |
| Installed-wheel malicious YAML | PASS | Direct and registry paths fail safely. |
| Mutation harness | PASS | 18/18 caught. |
| Manual mutation | PASS | Old defect caused targeted tests to fail. |

Final:

```text
PHASE_2A_READY
PHASE_2B_READY
PHASE_2C_NOT_STARTED
```

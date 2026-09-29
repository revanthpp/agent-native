# OpenAPI Adapter Error-Boundary Remediation

finding: V2-AUDIT-001 — direct OpenAPI adapter calls leaked PyYAML `ConstructorError` for hostile YAML tags.
root_cause: parser/error normalization existed in the registry path but not at the canonical OpenAPI adapter boundary.
production_fix:
  - `load_openapi_document` uses `yaml.safe_load` and maps YAML, encoding, size, and object-shape failures to safe parse errors.
  - `OpenAPIAdapter.detect` and `parse` classify expected parser failures without exposing third-party exceptions.
  - `AdapterResult` retains legacy string errors and adds status/error-code/protocol/artifact/provenance evidence through `AdapterError`.
  - `AdapterRegistry` retains malformed candidate evidence and distinguishes unexpected internal failures.
tests_added:
  - `tests/protocols/test_openapi_error_boundary.py`
  - unsafe Python tags, custom tags, malformed YAML, valid JSON/YAML, direct public operations, provenance, public rendering, MCP/A2A malformed inputs, and registry consistency.
mutation_added:
  - `M-ADAPTER-YAML-ERROR` in `scripts/run_phase2b_mutations.py` bypasses the production parser-error normalization seam and verifies the direct hostile-YAML regression catches the escape.
builder_verification:
  status: PASS
  targeted_tests: 20 passed, 23 subtests
  pytest: 84 passed, 158 subtests
  unittest: 84 OK
  pip_check: clean
  package: wheel and sdist built; package verifier passed with runtime_files=67
  installed_wheel: CLI smoke and hostile direct-vs-registry boundary smoke passed
  production_seam_mutations: 18/18 caught, including the new adapter-error mutation
ready_for_reaudit: true

The independent audit artifacts under `audit_v2/` are prior-run evidence and
were not modified. The builder must not promote Phase 2A or Phase 2B to final
READY; a different model must rerun the release gates before Phase 2C begins.

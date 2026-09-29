# Remediation Backlog

## V2-AUDIT-001

Severity: Medium

Direct OpenAPI malicious YAML handling leaks `yaml.constructor.ConstructorError` from `OpenAPIAdapter.detect()` and `OpenAPIAdapter.parse()`.

Expected behavior:

- `detect()` should return `False` for malformed or unsafe YAML.
- `parse()` should return an `AdapterResult` with `validity=INVALID` or an explicit limitation/error.
- The adapter should not require callers to use `AdapterRegistry` to receive fail-safe behavior.

Suggested fix:

- In `load_openapi_document`, catch `yaml.YAMLError` and re-raise `ValueError`.
- In `OpenAPIAdapter.parse`, catch `ValueError` and return a structured invalid `AdapterResult`.
- Add a test with `!!python/object/apply:os.system [...]` for both direct adapter and registry paths.

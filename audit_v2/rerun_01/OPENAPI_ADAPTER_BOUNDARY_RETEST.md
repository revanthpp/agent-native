# OpenAPI Adapter Boundary Retest

## Verdict

The prior `ConstructorError` finding is independently closed.

## Fresh Hostile Fixtures

Tested direct `OpenAPIAdapter.detect()` and `OpenAPIAdapter.parse()` plus registry path with:

- `!!python/object/apply:os.system ["echo audit-test"]`
- `!!python/object/new`
- `!!python/name`
- unknown custom YAML tag
- malformed YAML syntax

## Results

- Direct `detect()` returned `False`.
- Direct `parse()` returned status `INVALID`.
- Registry returned status `INVALID`.
- No raw `ConstructorError` escaped.
- No `os.system` execution occurred.
- Error message was sanitized: `YAML document could not be safely parsed`.
- Error code was `OPENAPI_YAML_PARSE_INVALID`.
- Artifact provenance was retained through `ProtocolArtifact` and `AdapterError.sanitized_details`, including source URI, content hash, and `parser-input` acquisition evidence.
- CLI rendering exposed structured JSON and no traceback/raw hostile payload.

## Internal Error Separation

A controlled `RuntimeError` from a subclassed OpenAPI adapter remained distinguishable from target-input failures:

- direct call propagated `RuntimeError`;
- registry returned status `ERROR` with `ADAPTER_FAILURE`.

This confirms remediation did not blanket-catch every exception as invalid YAML.

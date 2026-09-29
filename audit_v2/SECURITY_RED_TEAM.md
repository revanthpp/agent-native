# Security Red Team

## Passed

- Unsafe `$ref` targets did not call the injected fetch function.
- Cross-origin redirect was blocked after final-URI revalidation.
- Signature tampering was rejected.
- Replay was rejected.
- Invalid integrity could not create a cryptographically verified identity through `from_integrity`.
- Delegation confused-deputy cases denied as expected.
- Secret redaction mutation was caught by the builder mutation script.

## Finding

`V2-AUDIT-001`: Direct OpenAPI malicious YAML handling is not fail-closed at the adapter API. Safe YAML prevented object construction, but the exception escaped from `detect()` and `parse()`.

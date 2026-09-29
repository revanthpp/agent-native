# Mutation Retest

## Builder Harness

Command:

```bash
PYTHONPATH=src .audit-rerun-env/bin/python scripts/run_phase2b_mutations.py
```

Result: `18/18 caught`.

The harness includes meaningful production-seam coverage for:

- ownership;
- signature;
- replay;
- delegation expiry/revocation/bindings;
- explicit deny;
- default deny;
- policy version/staleness;
- redaction;
- unsafe remote `$ref`;
- adapter YAML error boundary.

`M-ADAPTER-YAML-ERROR` mutates the canonical OpenAPI parser-error normalization seam with `OpenAPIAdapter` and hostile YAML. It is not a toy helper or duplicate runtime.

## Manual Mutation

Created audit-only copy under:

```text
audit_v2/rerun_01/tmp/manual_mutation/
```

Manual changes in the copy:

- removed `yaml.YAMLError` normalization in the OpenAPI parser;
- removed adapter catches for `yaml.YAMLError`.

Command:

```bash
PYTHONPATH=src ../../../../.audit-rerun-env/bin/python -m pytest tests/protocols/test_openapi_error_boundary.py -q
```

Result:

- 16 failed/subfailed checks;
- failures included direct `detect`, `parse`, `validate`, `normalize`, enumeration operations, registry consistency, hostile YAML normalization, and CLI sanitization.

Conclusion: the old defect is test-sensitive.

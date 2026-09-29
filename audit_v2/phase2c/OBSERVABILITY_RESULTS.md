# Observability Results

Result: pass.

Evidence:

- CLI dry-run and execution emitted trace JSON.
- Receipt `trace_id` and `correlation_id` matched trace roots.
- Independent secret trace probe redacted authorization and API-key-like values.
- OTEL-compatible export shape was present.

Files:

- `audit_v2/phase2c/results/cli_dry_trace.json`
- `audit_v2/phase2c/results/cli_trace.json`
- `audit_v2/phase2c/results/stress_checks.json`

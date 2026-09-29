# Dry-Run Results

Result: fail.

The normal synthetic adapter dry-run is non-mutating, and the official test
`test_dry_run_does_not_change_adapter_state` passed. Independent stress testing
with a mutating audit adapter showed the simulator still calls
`selected_adapter.prepare()` and `selected_adapter.preview()` before the
`dry_run` branch returns.

Evidence:

- `audit_v2/phase2c/results/stress_checks.json`
- Check: `dry_run_preview_prepare_side_effect_trap`
- Expected snapshot: version `1`
- Actual snapshot: version `3`
- Reported status: `WOULD_ALLOW`

Code path:

- `src/agentnative/simulator/engine.py:184-192`

Finding: `P2C-003`.

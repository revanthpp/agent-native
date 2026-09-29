# Mutation Results

Result: pass for shipped mutation harnesses.

Phase 2C:

- Command: `.audit-phase2c/bin/python scripts/run_phase2c_mutations.py`
- Result: 15/15 caught.
- Evidence: `audit_v2/phase2c/results/phase2c_mutations.json`

Phase 2B regression:

- Command: `.audit-phase2c/bin/python scripts/run_phase2b_mutations.py`
- Result: command exited 0.
- Evidence: `audit_v2/phase2c/results/phase2b_mutations.json`

Gap:

- The shipped Phase 2C mutation set does not include malformed economic values,
  dry-run mutating preview/prepare, or concurrent idempotency races.

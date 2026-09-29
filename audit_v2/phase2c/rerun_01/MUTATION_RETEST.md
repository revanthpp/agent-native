# Mutation Retest

Result: PASS for shipped mutation suites.

Phase 2B:

- Command: `.phase2c-rerun/bin/python scripts/run_phase2b_mutations.py`
- Result: `18/18` caught.
- Evidence: `results/phase2b_mutations.json`

Phase 2C:

- Command: `.phase2c-rerun/bin/python scripts/run_phase2c_mutations.py`
- Result: `23/23` caught.
- Evidence: `results/phase2c_mutations.json`

Manual audit mutations:

- risk ceiling comparison disabled: test detected unsafe execution;
- atomic idempotency disabled: test produced 8 side effects;
- dry-run purity disabled: test invoked active `prepare()` and `preview()`.

Gap:

- shipped mutations do not catch the request-hash omissions for principal,
  agent, and environment, nor confirmation-before-idempotency replay ordering.

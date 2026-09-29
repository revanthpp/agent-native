# Security Red Team Results

Result: fail because risk-ceiling malformed-input bypasses execute.

Passed red-team checks:

- receipt tamper detection;
- receipt secret minimization;
- trace secret redaction;
- confirmation replay;
- confirmation context mismatch;
- stale quote rejection;
- hidden read mutation rejection through official tests.

Failed red-team checks:

- `NaN` value executed;
- negative value executed;
- wrong currency executed;
- missing currency executed;
- dry-run mutation trap changed adapter state;
- concurrent same-key execution duplicated side effects.

Security verdict:

- Phase 2C should stay blocked until the three P1 findings are remediated.

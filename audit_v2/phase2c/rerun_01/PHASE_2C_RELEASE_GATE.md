# Phase 2C Release Gate

Final gate: `PHASE_2C_NOT_READY`.

Ready criteria met:

- original malformed money P1 closed;
- original same-key duplicate side-effect race closed for one logical request;
- original dry-run active-path P1 closed;
- clean env and wheel pass;
- mutation suites pass;
- package verification passes;
- receipts/traces remain coherent.

Ready criteria not met:

- same-key/different-principal, different-agent, and different-environment
  requests do not fail closed;
- canonical idempotency request hash omits material authorization dimensions;
- same-key confirmed retry fails with `CONFIRMATION_REPLAY` before idempotency
  can replay success.

Phase 2D remains forbidden. Remediate only the remaining Phase 2C release
blockers and rerun this audit.

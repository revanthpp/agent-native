# Phase 2C Acceptance Thresholds

Release blockers are zero tolerance for unauthorized execution, risk-ceiling
breach, destructive execution without confirmation, duplicate required side
effects, stale quote commit, hidden mutation, forged receipt acceptance, raw
secret in a receipt/trace, production environment escape, unbounded retry, or
stale `ALLOW` after policy changes to `DENY`.

Functional thresholds:

- 100% mandatory simulator and transaction fixtures pass with zero skips;
- every state-changing result has a receipt;
- every receipt verifies and correlates to its trace;
- all public outputs contain hashes/references rather than raw secrets;
- every critical Phase 2C mutation is caught;
- v1, Phase 2A, and Phase 2B suites remain green.

Performance baselines remain advisory: policy evaluation under 50 ms p95 and
receipt generation under 25 ms p95 in the controlled reference environment.

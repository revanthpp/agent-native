# Phase 2C Requirements Reconstruction

Reconstructed mandatory requirements from the Phase 2C audit directive, release
review, architecture docs, governance docs, and acceptance thresholds:

- verified ownership and environment matching before active simulation;
- explicit state machine with invalid transitions rejected;
- environment/action/value/currency risk ceilings enforced before commit;
- dry-run must not change state;
- preview must issue a quote bound to principal, business, environment,
  capability, resource, value, currency, and version;
- stale quote, expired quote, and resource-version TOCTOU must be rejected;
- required confirmation must bind to the exact quote and be single-use;
- idempotency must prevent duplicate side effects, including retry and
  concurrent same-key scenarios;
- retries must be bounded and observable;
- partial outcomes and compensation must be explicit;
- hidden mutations in read/preview actions must fail closed;
- receipts must be minimized, redacted, integrity-protected, and verifiable;
- traces must be redacted and correlate with receipts;
- package and CLI behavior must match source behavior;
- Phase 2A and Phase 2B guarantees must remain green.

These requirements are stricter than the current unit test coverage in the
malformed-value, dry-run trap, and concurrent-idempotency areas.

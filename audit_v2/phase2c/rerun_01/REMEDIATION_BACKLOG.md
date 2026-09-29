# Remediation Backlog

## P1: Bind idempotency request hash to material authorization context

- Include principal reference.
- Include agent ID and provider ID.
- Include business ID and target environment.
- Consider quote ID and confirmation ID when they exist and are semantically
  part of the same logical request.
- Preserve exclusion of volatile metadata such as trace IDs and timestamps.
- Add tests for same key with changed amount, currency, resource, principal,
  agent, capability, environment, quote, confirmation, and payload.

## P1: Reorder idempotency replay and confirmation consumption safely

- For same key and same canonical request hash, return existing successful
  idempotency result before consuming a confirmation replay token.
- For new key or changed hash, keep confirmation replay/binding checks strict.
- Add tests for:
  - same key + same confirmation + same request replay;
  - new key + old confirmation rejected;
  - same key + changed request + old confirmation rejected/conflicted;
  - receipt semantics for replayed confirmed request.

## P2: Tighten release wording for dry-run trust boundary

- Say dry-run never calls active Agent Native execution methods.
- Say `build_plan()` is trusted/pure adapter code.
- Avoid implying arbitrary hidden external side effects inside adapter code are
  generically detected.

## Required re-audit

- Rerun `audit_v2/phase2c/rerun_01/tools/final_phase2c_reaudit.py`.
- Require request-hash and confirmation/idempotency sections to pass.
- Rerun clean env, wheel, package verifier, and mutation suites.

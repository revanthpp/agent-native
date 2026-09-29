# Agent Native v2 Phase 2C Final Re-Audit

## 1. Executive Verdict

`PHASE_2C_NOT_READY`

The remediation closed the original broad money, atomic same-request
concurrency, and dry-run active-path P1s. However, the final directive also
requires same-key/different-request conflicts across material dimensions and
same-key confirmed retry replay. Those checks still fail.

Summary evidence:

- Independent final harness: `54/59` passed.
- Money retest: `23/23` passed.
- Concurrency retest: `4/4` passed; duplicate side-effect rounds `0`.
- Dry-run retest: `5/5` passed with a trust-boundary observation.
- Changed-request idempotency: `5/8` passed; principal, agent, environment failed.
- Request-hash audit: `0/1` passed.
- Clean pytest: `109 passed`.
- unittest discovery: `84 passed`.
- Phase 2B mutations: `18/18` caught.
- Phase 2C mutations: `23/23` caught.
- Package verifier: `PACKAGE_CONTENT_VALID runtime_files=78`.

## 2. Original P1 Closure Matrix

| Original P1 | Retest | Result |
| --- | --- | --- |
| malformed value/currency bypass | hostile money matrix and installed-wheel malformed scenario | PASS |
| concurrent idempotency race | barrier-before-call, slow side-effect, scheduler pressure | PASS for same logical request |
| dry-run state mutation | instrumented active adapter and hostile plan adapter | PASS for Agent Native active path |

All three original P1 classes are closed in their original shape, but Phase 2C
cannot be marked ready because two new HIGH findings remain in the stricter
idempotency contract.

## 3. Monetary Risk Results

The implementation now models money as a domain invariant. The audit validated
finite, non-negative, exact `Decimal` semantics with inclusive `100.00 USD`
ceiling behavior. Invalid values did not reach adapter execution.

Passed cases included:

- `0`, `0.01`, `99.99`, `100.00` USD allowed.
- `100.01`, negatives, `NaN`, infinities, `None`, booleans, numeric strings,
  huge decimals, missing currency, wrong currency, and unsupported currency
  denied.
- lowercase and whitespace currency normalized to `USD`.
- no FX conversion.

Installed wheel check: `"NaN"` scenario returned `DENIED`,
`RISK_VALUE_INVALID`, exit code `3`.

## 4. Atomic Idempotency Results

Same logical request concurrency passed:

- Harness A: 8 workers x 25 rounds, one side effect each round.
- Harness A: 32 workers x 10 rounds, one side effect each round.
- Harness B: slow blocked owner; only one worker entered `execute()`;
  waiters replayed coherently.
- Harness C: 8 workers x 100 rounds under jitter; duplicate side-effect rounds
  `0`.

Failure and liveness checks passed:

- owner failure before side effect recovered on retry with one effect;
- owner failure after side effect became `UNKNOWN_OUTCOME` and blocked retry;
- waiter timeout returned bounded `IDEMPOTENCY_IN_PROGRESS`;
- lost response after successful commit retried with one logical effect.

Failures:

- same-key changed principal replayed success instead of conflict;
- same-key changed agent replayed success instead of conflict;
- same-key changed environment replayed success instead of conflict;
- request hash omitted principal, agent, and environment;
- same-key confirmed retry failed with `CONFIRMATION_REPLAY`.

## 5. Original Fixture Adjudication

Classification: `TEST_DESIGN_FLAW`.

The old fixture placed a barrier inside adapter `execute()`. Correct
single-flight logic should allow only one worker to enter `execute()`, so a
barrier that requires every worker to arrive inside `execute()` is incompatible
with the corrected architecture.

Answers:

1. The barrier was located inside the fake adapter `execute()` method.
2. Yes, it required multiple workers to enter a method single-flight should
   permit only one worker to enter.
3. Yes, after atomic pre-claim it can deadlock/fail because only the owner
   reaches `execute()`.
4. No, the BRD requires one logical side effect, not all workers entering the
   downstream execution method.
5. Removing that fixture does not weaken the invariant if replaced by
   before-transaction barriers and slow-owner PENDING tests.
6. Yes, the invariant is better tested with a barrier before transaction call.
7. The builder replacement was directionally adversarial, and the independent
   harness reproduced the same guarantee with 8, 32, and jittered workers.
8. Yes, independent harnesses reproduced exactly one side effect for one
   logical request.

## 6. Dry-Run Purity Results

The dry-run active-path defect is closed.

Observed dry-run invocation counts:

```json
{
  "constructor": 1,
  "build_plan": 1,
  "prepare": 0,
  "preview": 0,
  "execute": 0,
  "verify": 0,
  "compensate": 0
}
```

Active `prepare()` / `preview()` / `execute()` were not called, and active
adapter mutation produced `business_state_delta == 0`.

Mutating `build_plan()` that changed adapter-visible snapshot failed closed as
`DRY_RUN_SIDE_EFFECT`.

## 7. Dry-Run Trust Boundary

The defensible claim is:

> Dry-run never invokes Agent Native active execution methods. It calls a
> contractually pure adapter `build_plan()` and fails closed when
> adapter-visible snapshot changes.

The audit also proved that an arbitrary `build_plan()` can mutate an external
store without changing adapter-visible snapshot. That is not generically
detectable by Agent Native. Documentation mostly states the correct trusted
adapter contract, so this is not a release blocker; release language should
avoid implying arbitrary untrusted dry-run code is side-effect-proof.

## 8. Cross-Control Regressions

Passed:

- valid amount plus required confirmation returned `AWAITING_CONFIRMATION`;
- quote/TOCTOU blocked resource change after preview;
- old confirmation with new key was rejected;
- idempotency claim did not override policy recheck;
- delegation revocation before commit failed closed.

Failed:

- same logical retry with same key and same confirmation returned
  `CONFIRMATION_REPLAY` instead of replaying the idempotent success.

## 9. Receipt / Trace Results

Passed:

- successful owner request receipt verified and correlated to trace;
- conflict receipt did not report success;
- denied malformed money receipt reported `DENIED` with `side_effect=NONE`;
- dry-run receipt reported `DRY_RUN` with `side_effect=NONE`.

## 10. Clean Environment / Wheel

Clean environment:

- `.phase2c-rerun`
- `pip check`: clean
- `pytest`: `109 passed`
- `unittest discover`: `84 passed`

Wheel:

- built `dist/agentnative-2.0.0a1-py3-none-any.whl`;
- installed into `.phase2c-rerun-wheel`;
- `agentnative --version`: `2.0.0a1`;
- wheel `pip check`: clean;
- package verifier: `PACKAGE_CONTENT_VALID runtime_files=78`;
- CLI dry-run, execute, receipt verify passed;
- CLI malformed money denial returned exit code `3`;
- installed API same-key same-request replay and changed amount conflict passed.

Network note: initial package-resolution operations failed under the sandbox and
passed with explicit package-index escalation.

## 11. Mutation Results

- Phase 2B mutation suite: `18/18` caught.
- Phase 2C mutation suite: `23/23` caught.
- Manual audit mutations were sensitive:
  - disabling ceiling comparison executed `100.01`;
  - disabling atomic idempotency produced 8 side effects;
  - disabling dry-run purity invoked active `prepare()` and `preview()`.

## 12. New Findings

- `P2C-RR-001` HIGH: idempotency request hash omits principal, agent, and environment.
- `P2C-RR-002` HIGH: same-key confirmed retry is rejected before idempotency replay.

## 13. Release Gate Matrix

See `RELEASE_GATE_MATRIX.md`.

## 14. Remediation Backlog

See `REMEDIATION_BACKLOG.md`.

## 15. Principal Engineer Assessment

- Monetary risk is now modeled as a real domain invariant rather than a loose numeric comparison.
- Atomic idempotency is real for one same logical request in one process.
- If the idempotency owner crashes after side effect, current reference semantics become `UNKNOWN_OUTCOME` and block unsafe retry in-process.
- Dry-run has an architectural purity boundary, but `build_plan()` remains trusted adapter code.
- The builder's claim about the old barrier fixture is correct.
- Process-local idempotency remains reference-grade and documented, not distributed production idempotency.
- Release language should avoid saying arbitrary mutating `build_plan()` behavior is generically prevented.

## 16. Next Action

Remediate only the remaining release blockers and rerun this audit.

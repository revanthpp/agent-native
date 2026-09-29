# Concurrency Fixture Adjudication

Classification: `TEST_DESIGN_FLAW`.

The old failed stress fixture placed a barrier inside adapter `execute()`. That
fixture was useful against the pre-remediation check-then-record implementation,
but it is not valid against an atomic pre-claim single-flight design because
correct behavior permits only one worker to enter `execute()`.

Answers:

1. Barrier location: inside fake adapter `execute()`.
2. It required multiple workers to enter a method that correct single-flight
   logic should permit only one worker to enter.
3. It can deadlock/fail after remediation because waiters should block at the
   idempotency layer, not inside adapter execution.
4. That assumption was not part of the BRD.
5. Removing the fixture does not weaken the invariant if replaced by
   before-call, slow-owner, and jittered scheduler harnesses.
6. The original invariant is better tested with a barrier before transaction
   call.
7. The builder replacement was directionally adversarial; the independent
   harness added 8-worker, 32-worker, slow-owner, and 100-round jittered checks.
8. Independent harnesses reproduced exactly one side effect for one logical
   same-key request.

Important distinction:

The fixture is invalid after the architecture change, but the final idempotency
contract still has separate request-hash and confirmation-ordering defects.

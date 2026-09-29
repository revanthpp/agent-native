# P1 Idempotency Retest

Result: PARTIAL / NOT READY.

Closed:

- same logical request concurrency produced at most one side effect;
- PENDING waiters replayed the owner result;
- owner failure before side effect recovered safely;
- owner failure after side effect produced `UNKNOWN_OUTCOME`;
- waiters timed out instead of hanging forever;
- lost response after successful commit produced one logical side effect;
- same key with changed amount/resource/capability/payload failed or denied.

Still failing:

- same key with changed principal replayed `EXECUTED`;
- same key with changed agent replayed `EXECUTED`;
- same key with changed environment replayed `EXECUTED`;
- canonical request hash does not bind principal, agent, or environment;
- same key/same confirmation retry failed with `CONFIRMATION_REPLAY`.

Conclusion: original duplicate side-effect race is closed, but the final
idempotency contract remains blocked by `P2C-RR-001` and `P2C-RR-002`.

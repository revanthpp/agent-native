# Release Gate Matrix

| Gate | Result | Evidence |
| --- | --- | --- |
| Original P1 money/value/currency | PASS | money `23/23`, wheel malformed denial |
| Original P1 concurrent duplicate effect | PASS | Harnesses A/B/C, duplicate rounds `0` |
| Original P1 dry-run active mutation | PASS | build_plan only; active methods `0` |
| Same-key changed amount/resource/capability/payload | PASS | conflict/deny without second effect |
| Same-key changed principal | FAIL | replayed `EXECUTED` |
| Same-key changed agent | FAIL | replayed `EXECUTED` |
| Same-key changed environment | FAIL | replayed `EXECUTED` |
| Request hash material coverage | FAIL | principal/agent/environment omitted |
| Same-key confirmed retry | FAIL | `CONFIRMATION_REPLAY` before replay |
| Unknown outcome safety | PASS | retry blocked as `IDEMPOTENCY_UNKNOWN_OUTCOME` |
| Waiter liveness | PASS | bounded `IDEMPOTENCY_IN_PROGRESS` |
| Process-local limitation documented | PASS | governance and ADR-022 |
| Risk + confirmation | PASS | within ceiling still requires confirmation |
| Risk + quote/TOCTOU | PASS | changed resource blocked |
| Policy/delegation recheck | PASS | fail-closed |
| Receipt/trace | PASS | valid/correlated; denied/conflict not success |
| Clean environment | PASS | `109 passed`; `pip check` clean |
| Installed wheel | PASS | CLI smoke and package verifier |
| Phase 2B mutations | PASS | `18/18` |
| Phase 2C mutations | PASS | `23/23` |

Final result: `BLOCKED`.

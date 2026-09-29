# Phase 3B Independent Review Result

Reviewed commit: `6ac1113ebf032c60856c4722150481cd5441e1cd`
Reviewer identity/model: Codex in current workspace
Review date: 2026-09-29 local
Environment: macOS 26.6.2, Python 3.14.3, SQLite 3.53.3

## Verdict

`PHASE_3B_NOT_READY`

This short adversarial pass reproduced the main source-test counts, but found a high-severity provenance verifier failure and a high-severity mutation-evidence weakness. The verdict is limited to this audit pass; many external-plan phases remain explicitly `NOT_TESTED`.

## Gate Summary

| Gate | Result | Evidence |
|---|---|---|
| Pinned commit | PASS | `git rev-parse HEAD` matched the requested SHA. |
| Baseline source tests | PASS | `148 passed, 158 subtests passed`; unittest `105 OK`. |
| Evidence verifier | FAIL | Tampered manifests with missing artifacts, arbitrary SHAs, and fabricated CI were accepted. |
| Mutation evidence | FAIL | Phase 3 harness reports `20/20`, but many reported mutations are not real production mutations. |
| Wheel smoke | PARTIAL PASS | Passed with network access; script still uses `--system-site-packages` and checkout examples. |

## Findings

| ID | Severity | Requirement | Expected | Actual | Evidence |
|---|---|---|---|---|---|
| P3B-AUDIT-001 | HIGH | Evidence provenance | Reject missing/fabricated evidence | Accepted all five tamper cases | `findings.json`, `evidence_tamper_matrix.py` |
| P3B-AUDIT-002 | HIGH | Real mutation testing | Mutate production behavior | Many `lambda: False` contrasts; literal SHA-string comparison | `scripts/run_phase3_mutations.py` |
| P3B-AUDIT-003 | MEDIUM | Reproducible environment | Clear source/wheel target | `.venv` default imports site-packages; source requires `PYTHONPATH=src` | `environment.json` |

## Reproduced Builder Claims

| Claim | Reproduced? | Independent evidence |
|---|---|---|
| `148` pytest tests and `158` subtests | YES | Source run with `PYTHONPATH=src`. |
| `105` unittest checks | YES | Source run with `PYTHONPATH=src`. |
| Phase 3 `20/20` mutations caught | NUMERICALLY YES, SEMANTICALLY NO | Harness returns success but does not provide reliable mutation proof. |
| Evidence verifier validates manifest | YES FOR ORIGINAL, FAILS UNDER TAMPER | Original manifest returns valid; tampered manifests also return valid. |
| Wheel smoke passes | YES WITH NETWORK | Escalated network run passed. |

## Untested Areas

Full schema/parser adversarial matrix, independent recommendation oracle, all-scenario durable state assertions, crash-boundary injection, multiprocess concurrency, full provenance/CI verification through GitHub APIs, and full CLI artifact-safety matrix were not completed in this pass.

## Required Remediation

1. Harden `scripts/verify_phase3b_evidence.py` to require non-empty artifact entries, require every artifact path to exist, verify every digest, validate commit SHAs against git/GitHub, and validate CI run metadata against the reviewed commit.
2. Replace Phase 3 mutation harness cases that use `lambda: False` or literal comparisons with real temporary source mutations or monkeypatched production seams, and map each mutation to a failing test.
3. Make source, editable, and wheel test environments explicit so baseline commands cannot silently exercise stale site-packages code.

# Phase 3B Gate 2 Proof Remediation Builder Report

Date: 2026-09-29

## Honest status

```text
READY_FOR_PHASE_3B_GATE2_RERUN
```

This is builder evidence only. The preserved independent audit remains `PHASE_3B_NOT_READY` until a different reviewer reruns the package and publishes a separate verdict.

## What changed

| Gate 2 control | Implementation | Proof |
| --- | --- | --- |
| Versioned evidence manifest | `V3/evidence/phase3b_evidence_manifest.schema.json`, `scripts/verify_phase3b_evidence.py` | strict top-level, CI, artifact, command, and result contracts |
| Fail-closed artifact verification | safe repository-relative path resolution, regular-file checks, exact SHA-256 and byte-size checks, required role inventory | 30-case tamper matrix |
| Provenance and CI binding | real Git commit existence/ancestry checks; GitHub Actions run/head/workflow/conclusion/artifact digest validation; explicit offline partial status | known-good online plus offline-partial cases |
| Honest mutation score | isolated source copies, exact-one target checks, diff capture, subprocess oracles, timeout/invalid/survivor classifications | 20 required Phase 3 mutants, 20 killed, zero survivors/invalid/timeouts |
| Hermetic wheel proof | no system-site packages, copied inputs outside checkout, cleared import path, `agentnative.__file__` assertion, `pip check`, `pip freeze` | wheel smoke result with import path |
| Audit handoff | original audit preserved unchanged under `audit_v3/phase3b_closure/rerun_01/` | separate independent rerun package |

## Mutation scoreboard

The result artifact is machine-readable at `V3/evidence/gate2/phase3_mutation_result.json`. Each mutant records its production file, target hash, applied diff, named detecting test, subprocess exit code, classification, duration, and output digest. The required score is `20 / (20 + 0) = 1.0`; invalid, timed-out, and excluded cases are not counted as killed.

## Proof boundary

The package remains synthetic and builder-authored. It does not prove live connector behavior, payment-network settlement, production credentials, protocol certification, legal compliance, or operational readiness. No builder workflow may change the status to `PHASE_3B_INDEPENDENTLY_VERIFIED`.

The GitHub proof topology is intentionally two-stage: `ci.yml` builds and uploads the builder bundle, then `gate2-external-verification.yml` is triggered by the completed builder run, binds the manifest to that completed run and its artifact digest, and performs the online verification from a separate workflow context. This prevents a workflow from claiming its own still-running status is completed.

The current local regression baseline is `149 passed, 158 subtests passed` under pytest and `105 tests, OK` under the stdlib unittest suite. The generated Gate 2 manifest records the exact run-specific counts; these numbers are builder evidence, not an independent verdict.

## Reproduction

```bash
PYTHONPATH=src .venv/bin/python scripts/run_phase3b_evidence_tamper_matrix.py
PYTHONPATH=src .venv/bin/python scripts/run_phase3_mutations.py --output V3/evidence/gate2/phase3_mutation_result.json
PYTHONPATH=src .venv/bin/python scripts/run_phase3b_wheel_smoke.py dist/agentnative-*.whl --result-output V3/evidence/gate2/wheel_smoke_result.json
PYTHONPATH=src .venv/bin/python scripts/run_phase3b_gate2_evidence.py
PYTHONPATH=src .venv/bin/python scripts/verify_phase3b_evidence.py V3/evidence/gate2/phase3b_gate2_builder_manifest.json --offline
```

The offline verifier reports `OFFLINE_PARTIAL_VERIFICATION` by design. Online verification requires GitHub authentication and validates the actual completed run and uploaded artifact.

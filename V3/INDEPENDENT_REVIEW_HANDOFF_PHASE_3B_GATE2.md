# Independent Review Handoff — Phase 3B Gate 2

## Builder status

```text
READY_FOR_PHASE_3B_GATE2_RERUN
```

The prior audit result is preserved and remains authoritative until independently rerun:

- `audit_v3/phase3b_closure/rerun_01/INDEPENDENT_REVIEW_RESULT.md`
- `audit_v3/phase3b_closure/rerun_01/evidence_tamper_matrix.py`
- `audit_v3/phase3b_closure/rerun_01/HASHES.txt`

Do not edit those files or convert the builder status into an independent verdict.

## Reviewer commands

Run from a clean checkout of the reviewed commit with GitHub API access:

```bash
python -m pip install -e ".[dev]"
PYTHONPATH=src python scripts/run_phase3b_evidence_tamper_matrix.py
PYTHONPATH=src python scripts/run_phase3_mutations.py --output V3/evidence/gate2/phase3_mutation_result.json
python -m build
PYTHONPATH=src python scripts/run_phase3b_wheel_smoke.py dist/agentnative-*.whl --result-output V3/evidence/gate2/wheel_smoke_result.json
PYTHONPATH=src python scripts/run_phase3b_gate2_evidence.py
python scripts/verify_phase3b_evidence.py V3/evidence/gate2/phase3b_gate2_builder_manifest.json
```

The last command must contact GitHub and return `EVIDENCE_VALID`. `--offline` is permitted only for local debugging and must report `OFFLINE_PARTIAL_VERIFICATION`.

## Review questions

1. Does every tamper case fail with `EVIDENCE_INVALID` and a structured error containing `error_code`, `json_path`, `message`, and `remediation`?
2. Are all 20 mutants real source changes in isolated copies, and is every kill attributable to the named independent oracle?
3. Does the verified GitHub run have the same `head_sha` as `reviewed_commit_sha`, and does the uploaded artifact digest match GitHub?
4. Does the wheel import from the temporary virtualenv rather than the source checkout?
5. Do the public status and machine-readable artifacts remain builder-only and synthetic?

The independent reviewer should publish a separate result under `V3/` or the review system. The builder must not modify this handoff to claim independent verification.

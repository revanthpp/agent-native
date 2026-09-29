# Phase 3B Closure Independent Review Handoff

Status: `READY_FOR_INDEPENDENT_REVIEW`  
Authority: builder handoff; not an audit result  
Scope: synthetic Retail productization and closure remediation only

## Reviewer entry point

Run from the repository root:

```bash
PYTHONPATH=src python -m pytest --import-mode=importlib -q tests/retail tests/packs
PYTHONPATH=src python -m pytest --import-mode=importlib -q tests/retail/test_closure_remediation.py
python -m build
python scripts/run_phase3b_wheel_smoke.py dist/agentnative-*.whl
```

Reproduce these first: `lost_response`, `expired_delegation`, `connector_outage`, `duplicate_refund`, and an unknown scenario. Inspect the contract object, side-effect count, reconciliation state, receipt chain, and synthetic boundary.

## Files to inspect

- `src/agentnative/retail_schema.py`
- `src/agentnative/retail_product.py`
- `src/agentnative/packs/retail.py`
- `src/agentnative/persistence.py`
- `tests/retail/test_closure_remediation.py`
- `scripts/run_phase3b_wheel_smoke.py`
- `scripts/verify_phase3b_evidence.py`
- `V3/PHASE_3B_CLOSURE_REMEDIATION_BUILD_REPORT.md`

## Review questions

1. Do malformed or contradictory workspaces fail with stable path/code/remediation errors?
2. Can a declared capability or claimed protocol profile promote a direct value-changing journey without verifiable evidence?
3. Does each scenario activate the named domain control rather than append a label after another failure?
4. Do restart and concurrent last-item tests preserve one authoritative side effect and bounded inventory?
5. Are source SHA, evidence SHA, CI identity, and artifact digests sufficient to reproduce the exact builder claim?

The reviewer must author a separate result. Builder evidence must not be changed to `INDEPENDENTLY_VERIFIED` by this repository’s build process.

# Phase 2C Final Independent Rerun Handoff

Status: `BLOCKED` / `PHASE_2C_NOT_READY`  
Authority: preserved independent boundary; this is a rerun request, not a new verdict

The Phase 3B closure build does not self-promote Phase 2C. The independent reviewer must rerun the historical identity, delegation, policy, confirmation, transaction, replay, receipt, concurrency, crash, and packaging corpus from the preserved `audit_v2/` and `evals/phase2c/` materials, then publish a separate signed or otherwise integrity-checkable result.

Suggested entry point:

```bash
PYTHONPATH=src python scripts/run_phase2b_mutations.py
PYTHONPATH=src python scripts/run_phase2c_mutations.py
PYTHONPATH=src python -m pytest --import-mode=importlib -q tests/transactions tests/simulator tests/receipts tests/security
```

No Phase 3B builder artifact satisfies this independent gate.

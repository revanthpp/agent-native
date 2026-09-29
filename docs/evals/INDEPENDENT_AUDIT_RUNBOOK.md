# Independent v2 audit handoff

This repository intentionally does not contain `audit_v2/`. The QA directive
requires those artifacts to be produced by a separate audit run, and the
builder must not manufacture them.

The independent reviewer should start from a clean checkout of this branch and
run:

```bash
python -m venv .venv-audit
.venv-audit/bin/python -m pip install -e ".[dev]"
.venv-audit/bin/python -m pip check
.venv-audit/bin/python -m pytest -q
PYTHONPATH=src .venv-audit/bin/python scripts/run_phase2b_mutations.py
```

The reviewer should then execute the independent directive in
`V2/AGENT_NATIVE_V2_INDEPENDENT_TEST.md` and create the required `audit_v2/`
files, including findings and the release-gate matrix. Until that happens,
`PHASE_2A_RELEASE_REVIEW.md` remains `PHASE_2A_NOT_READY` and
`PHASE_2B_RELEASE_REVIEW.md` remains `PHASE_2B_CONDITIONALLY_READY`.

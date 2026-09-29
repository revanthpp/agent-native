# v2 QA Traceability Repair

| Finding | Root cause | Architecture fix | Code | Regression test | Eval | Gate |
|---|---|---|---|---|---|---|
| QA-V2-001 | old rows pointed to deleted incubation paths | rebuilt table against root files | `docs/REQUIREMENTS_TRACEABILITY.md` | root suite | phase2a/2b manifests | open until PARTIAL rows close |
| QA-V2-002 | base class only exposed detect/parse | full adapter contract and extension registry | `protocols/base.py`, `registry.py` | `test_adapter_contract.py` | phase2a manifest | Phase 2A |
| QA-V2-003 | all remote refs were rejected | resolver now defaults to v1 `SafeFetcher` and revalidates same-origin redirects/private targets | `protocols/openapi/refs.py`, `acquisition/fetcher.py` | `test_openapi_refs.py`, `test_network_boundaries.py` | phase2a manifest | VERIFIED locally; independent audit still required |
| QA-V2-004 | mutation script used identical toy behavior | each mutation disables one actual authorization, redaction, or ref-network production seam | `policy/authorization.py`, `delegation/models.py`, `policy/engine.py`, `security/sanitize.py`, `protocols/openapi/refs.py`, `scripts/run_phase2b_mutations.py` | canonical control tests plus 17-case runner | phase2b manifest | VERIFIED locally; independent audit still required |
| QA-V2-005 | no reproducible audit directory/dev dependency set | added `[dev]`, clean-install instructions, package checks, and an explicit no-fabrication audit gate | `pyproject.toml`, `docs/evals/RUNNING_TESTS.md`, `.github/workflows/ci.yml` | clean install command and root suite | independent audit must be supplied separately | OPEN — builder does not fabricate `audit_v2/` |
| QA-V2-006 | linter omitted several mandatory rules | dedicated ten-rule linter | `policy/lint.py` | `tests/policy/test_lint.py` | phase2b manifest | verified locally |

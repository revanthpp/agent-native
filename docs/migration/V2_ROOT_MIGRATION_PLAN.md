# v2 Root Migration Plan

## Baseline

`main` remains the v1.0.0 release at tag `v1.0.0` and commit `525847f`. Work continues on `develop/v2`. The temporary `V2/` tree now contains only historical prompts, BRD, and QA source documents; active implementation lives under the root `src/agentnative` package.

## Promotion plan

1. Keep v1 scanner, acquisition, evidence, reporting, and security modules intact.
2. Promote v2 protocol, capability, ownership, identity, delegation, and policy modules into the canonical `agentnative` package.
3. Merge CLI commands while retaining `agentnative scan` compatibility.
4. Add PyYAML to the root runtime dependency set and extend CI with v2 clean-install tests.
5. Preserve v1 tests and fixtures as regression coverage.
6. Root verification passed; duplicate implementation source/tests and the incubation pyproject were removed from `V2/`. The BRD and prompts remain as historical inputs.

## Rollback

The release tag and `main` branch are untouched. If root migration fails, discard only the `develop/v2` branch changes; no tag rewrite or force push is required.

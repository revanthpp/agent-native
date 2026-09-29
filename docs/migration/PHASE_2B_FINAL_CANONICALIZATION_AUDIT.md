# Phase 2B Final Canonicalization Audit

| Item | Current source | Canonical target | Action |
|---|---|---|---|
| protocol adapters | former `V2/src/agentnative_v2` | `src/agentnative/protocols` | MERGE; incubation runtime removed |
| capability graph | former incubation module | `src/agentnative/capabilities` | MERGE |
| ownership | former incubation module | `src/agentnative/ownership` | MERGE |
| identity/signatures | former incubation modules | `src/agentnative/identity` | MERGE |
| delegation/policy | former incubation modules | `src/agentnative/delegation`, `src/agentnative/policy` | MERGE |
| v1 acquisition/reporting/security | v1 root | existing `src/agentnative/{acquisition,reporting,security}` | KEEP/REUSE |
| tests | former `V2/tests` and root tests | root `tests/` | MERGE; canonical smoke tests added |
| evals | former `V2/evals` | root `evals/` and root manifests | MERGE |
| package metadata | both pyprojects | root `pyproject.toml` | KEEP root; incubation pyproject removed |
| incubation runtime | `V2/src`, `V2/pyproject.toml` | none | REMOVE_AFTER_MIGRATION |

Verification: root package discovery now uses only `src`; production source contains no `agentnative_v2` or `v2core` imports; the former duplicate `src/agentnative/v2core.py` was removed; the root wheel content check rejects the deprecated namespace and `v2/src` paths. Archived prompts and BRD documents remain under `V2/` as historical inputs only.

# Agent Native v1.0.0 release review

Decision: `V1_RELEASE_READY`

Date: 2026-09-19

## Scope

This review covers the first public release of Agent Native after the v3.1 security remediation work and the final release-engineering pass.

## QA and security result

The latest independent QA report is [FINAL_INDEPENDENT_QA_V3_1.md](FINAL_INDEPENDENT_QA_V3_1.md).

- P0 findings: 0
- P1 findings: 0
- The reported P2 false positive for ordinary documentation language was fixed and covered by a regression test.
- Raw, bearer, percent-encoded, double-encoded, URI path, URI fragment, and safe-text regression cases pass.
- Mutation checks showed that disabling canonicalization, credential detection, URI sanitization, report validation, or limitation sanitization causes the relevant tests to fail.
- The final report boundary is independently validated after rendering.

## Verification commands

The release verification includes:

```text
PYTHONPATH=src:. python -m unittest discover -s tests
python -m compileall -q src tests scripts
python scripts/qa_identity.py
python -m pip check
python -m build
```

The clean-environment package check installs the built wheel without network access, runs `pip check`, starts the installed CLI, and scans a double-encoded credential fixture. The fixture must be reported as unsafe and must not leak the credential in output.

## Public documentation

- `README.md` explains the project in plain language and includes Mermaid architecture and flow diagrams.
- `CHANGELOG.md` records the v1.0.0 release.
- `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, and `GOVERNANCE.md` are present.
- The historical v0.1 and v3 hardening reports remain available as development evidence. This document is the release decision for v1.0.0.

## Known limitations

- This is a passive readiness assessment, not a guarantee that a business will work with every agent or protocol implementation.
- Results depend on the public material available at scan time.
- Some agent-facing standards and deployment-specific behavior require checks beyond this release.
- The scanner does not authenticate to private systems or perform business actions.

## Repository state

The release tag is `v1.0.0`. The final commit SHA and GitHub URL are recorded in the release handoff after the repository push completes.

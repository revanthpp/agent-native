# Agent Native v2

This directory is the historical v2 prompt, BRD, and QA archive. The active
implementation was migrated to the canonical root package so it can be tested
and signed off without publishing to GitHub.

## Current scope

- prompt and BRD inputs for the version-pinned adapter interface;
- the original incubation scope and historical release notes.

Install and test the active build from the repository root with
`python -m pip install -e ".[dev]"`; see
[`docs/evals/RUNNING_TESTS.md`](../docs/evals/RUNNING_TESTS.md).

Do not treat files under `V2/` as canonical implementation or release evidence.

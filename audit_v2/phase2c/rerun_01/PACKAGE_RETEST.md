# Package Retest

Result: PASS.

Artifact:

- `dist/agentnative-2.0.0a1-py3-none-any.whl`

Results:

- wheel build passed after explicit package-index escalation for isolated build
  dependencies;
- wheel installed into `.phase2c-rerun-wheel`;
- `agentnative --version`: `2.0.0a1`;
- wheel `pip check`: pass;
- package verifier: `PACKAGE_CONTENT_VALID runtime_files=78`;
- CLI dry-run: pass;
- CLI execution: pass;
- receipt verification: `VALID`;
- malformed money CLI scenario: `DENIED`, `RISK_VALUE_INVALID`, exit code `3`;
- installed package API same-key replay and changed-amount conflict passed.

The distributed artifact contains the money, dry-run, and normal atomic
same-key remediation behavior.

# Clean Environment Results

Environment:

- Source env: `.audit-phase2c`
- Wheel env: `.audit-phase2c-wheel-env`
- Package: `dist/agentnative-2.0.0a1-py3-none-any.whl`

Results:

- Editable install: pass after approved network access for build dependencies.
- `pip check`: pass, no broken requirements.
- Full tests: pass, `104 passed in 1.18s`.
- Wheel install: pass after approved network access for runtime dependencies.
- Wheel `pip check`: pass, no broken requirements.

Notes:

- Initial package operations failed inside the sandbox because DNS/network
  package resolution was unavailable. The same commands passed with explicit
  escalation.

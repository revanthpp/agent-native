# Clean Environment Results

## Editable install

- Created `.audit-env` with `python -m venv .audit-env`.
- First `pip install -e ".[dev]"` failed under sandboxed network while resolving `setuptools>=68`.
- Reran with approved network access; install succeeded.
- `.audit-env/bin/python -m pip check`: passed, `No broken requirements found.`
- `.audit-env/bin/python -m pytest -q`: `77 passed, 144 subtests passed in 1.34s`.
- `.audit-env/bin/python -m unittest discover -v`: `Ran 77 tests ... OK`.
- `PYTHONPATH=src .audit-env/bin/python scripts/run_phase2b_mutations.py`: 17/17 caught.

## Wheel install

- Built wheel with `.audit-env/bin/python -m pip wheel . -w audit_v2/wheelhouse` after approved network access.
- Wheel: `audit_v2/wheelhouse/agentnative-2.0.0a1-py3-none-any.whl`.
- Created `.audit-wheel-env`.
- Installed with `--no-index --find-links audit_v2/wheelhouse agentnative`.
- CLI smoke passed:
  - `agentnative --help`
  - `agentnative scan --help`
  - `agentnative protocols --help`
  - `agentnative capabilities --help`
  - `agentnative owner --help`
  - `agentnative policy --help`

## Residual

The ambient system Python still lacks pytest/cryptography and is not a valid audit runner. The clean audit environments are the authoritative results.

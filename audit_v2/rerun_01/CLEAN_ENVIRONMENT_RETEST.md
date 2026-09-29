# Clean Environment Retest

## Editable Environment

Created:

```bash
python -m venv .audit-rerun-env
```

Install:

```bash
.audit-rerun-env/bin/python -m pip install -e ".[dev]"
```

The first install attempt failed under sandboxed network while resolving `setuptools>=68`; rerun with approved network access succeeded.

## Results

- `.audit-rerun-env/bin/python -m pip check`: `No broken requirements found.`
- `.audit-rerun-env/bin/python -m pytest -q`: `84 passed, 158 subtests passed in 1.36s`.
- `.audit-rerun-env/bin/python -m unittest discover -v`: `Ran 84 tests ... OK`.
- No mandatory skips observed.

## Wheel Environment

Built:

```bash
.audit-rerun-env/bin/python -m pip wheel . -w audit_v2/rerun_01/wheelhouse
```

Installed:

```bash
python -m venv .audit-rerun-wheel-env
.audit-rerun-wheel-env/bin/python -m pip install --no-index --find-links audit_v2/rerun_01/wheelhouse agentnative
```

Installed CLI smoke passed for:

- `agentnative --help`
- `agentnative scan --help`
- `agentnative protocols --help`
- `agentnative capabilities --help`
- `agentnative owner --help`
- `agentnative policy --help`

Installed-wheel hostile YAML check passed:

- direct `OpenAPIAdapter.detect()` returned `False`;
- direct `parse()` returned `INVALID`;
- error code `OPENAPI_YAML_PARSE_INVALID`;
- registry returned `INVALID`.

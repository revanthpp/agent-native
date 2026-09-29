# Running tests

Create an isolated environment and install the runtime plus development dependencies:

```bash
python -m venv .venv-audit
.venv-audit/bin/python -m pip install -e ".[dev]"
.venv-audit/bin/python -m pip check
.venv-audit/bin/python -m pytest
```

The repository suite is also runnable without pytest through `python -m unittest discover -s tests`. Runtime dependencies are PyYAML and cryptography; pytest is test-only.

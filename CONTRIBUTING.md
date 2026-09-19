# Contributing

Small, reviewable changes are preferred. Every new check needs a stable ID, rationale, severity, evidence model, positive fixture, negative fixture, ambiguous or unknown fixture, and an entry in the check catalog and traceability matrix.

Before opening a pull request:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m agentnative checks
```

Security-sensitive changes must document the new threat surface and preserve the passive, no-side-effect boundary.

# Agent Native v3 Phase 3A Build Record

Status: `SUPERSEDED BY PHASE_3_BUILD_REPORT.md`

The follow-up Phase 3 Build Requirements BRD reclassifies the original seed SDK as `IMPLEMENTED_UNVERIFIED` and adds hard gates for core guarantees, lifecycle, provenance, typed evidence, protocol drift, adversarial verification, and the Retail reference journey. See [PHASE_3_BUILD_REPORT.md](PHASE_3_BUILD_REPORT.md) for the current builder status.

Phase 3A turns the v3 sector-pack contract into an executable extension point without changing the v2 control plane.

## Implemented

- `agentnative.packs` SDK with validated YAML manifests.
- Core-version compatibility enforcement and sector namespace validation.
- Canonical capability compilation into the existing `CapabilityGraph`.
- Reversible pack registry disable/enable behavior.
- Deterministic activation strategy recommendations with assumptions, tradeoffs, prerequisites, and recorded overrides.
- Dimension-specific maturity assessment with evidence gates and no composite score.
- Pack evaluation harness requiring positive, partial-maturity, deceptive, malformed, and high-risk scenarios.
- Requirement → control → evidence → evaluation → recommendation traceability validation.
- Seed packs for retail, healthcare administration, and local business/SMB.
- CLI inspection commands:

```bash
agentnative packs list
agentnative packs show sector.retail
```

## Deliberate scope boundary

The three built-in packs are `design` / `seed` packs. They provide the declarative contract and the first capability/evaluation inventory, but they do not claim sector release readiness, legal compliance, protocol conformance, production connector support, or payment execution.

Retail, healthcare, and local-business release gates remain Phase 3B–3D work. This prevents the SDK from confusing a useful sector taxonomy with an executable production integration.

## Path map

```text
builtin/*.yaml
  → PackLoader / PackRegistry
  → CapabilityProfile.to_capability
  → canonical CapabilityGraph
  → ActivationStrategyEngine / MaturityFramework / PackEvalHarness
  → v3 blueprint evidence and release gates
```

## Verification

`tests/packs/test_phase3a.py` covers load/compatibility, graph extension, reversible disablement, recommendation overrides, multidimensional maturity, eval corpus categories, and traceability validation.

The local checkout used for this build does not currently have the dev dependencies installed. Run the repository's normal environment setup before the full release suite:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

"""Sector-pack SDK for Agent Native v3.

Packs are additive data and evaluation bundles. They extend the canonical v2
capability model without changing core policy, identity, simulation, or
receipt behavior.
"""

from agentnative.packs.activation import (
    ActivationInputs,
    ActivationPattern,
    ActivationRecommendation,
    ActivationStrategyEngine,
)
from agentnative.packs.evidence import TraceabilityError, TraceabilityRecord, validate_traceability
from agentnative.packs.evals import EvalResult, PackEvalHarness
from agentnative.packs.loader import PackCompatibilityError, PackLoader, PackRegistry, load_builtin_packs
from agentnative.packs.maturity import DimensionAssessment, MaturityAssessment, MaturityFramework
from agentnative.packs.models import (
    CapabilityProfile,
    EvalScenario,
    EvalScenarioCategory,
    Pack,
    PackManifest,
)

__all__ = [
    "ActivationInputs",
    "ActivationPattern",
    "ActivationRecommendation",
    "ActivationStrategyEngine",
    "CapabilityProfile",
    "DimensionAssessment",
    "EvalScenario",
    "EvalScenarioCategory",
    "EvalResult",
    "MaturityAssessment",
    "MaturityFramework",
    "Pack",
    "PackCompatibilityError",
    "PackLoader",
    "PackManifest",
    "PackEvalHarness",
    "PackRegistry",
    "TraceabilityError",
    "TraceabilityRecord",
    "load_builtin_packs",
    "validate_traceability",
]

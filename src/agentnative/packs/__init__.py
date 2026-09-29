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
from agentnative.packs.core_gates import CoreGuarantee, CoreGuaranteeError, CoreGuaranteeRegistry
from agentnative.packs.evidence import EvidenceObservation, EvidenceState, EvidenceStore, TraceabilityError, TraceabilityRecord, validate_traceability
from agentnative.packs.evals import EvalResult, PackEvalHarness
from agentnative.packs.loader import PackCompatibilityError, PackLoader, PackRegistry, PackResourceLimitError, load_builtin_packs
from agentnative.packs.maturity import DimensionAssessment, MaturityAssessment, MaturityFramework
from agentnative.packs.models import (
    CapabilityProfile,
    EvalScenario,
    EvalScenarioCategory,
    Pack,
    PackLifecycleState,
    PackManifest,
)
from agentnative.packs.protocols import DriftResult, ProtocolDriftReport, ProtocolProfile, ProtocolRegistry
from agentnative.packs.retail import RetailActivationBlocked, RetailJourneyState, RetailOrder, RetailProduct, RetailQuote, RetailReferenceEnvironment, RetailResult, RetailVariant

__all__ = [
    "ActivationInputs",
    "ActivationPattern",
    "ActivationRecommendation",
    "ActivationStrategyEngine",
    "CoreGuarantee",
    "CoreGuaranteeError",
    "CoreGuaranteeRegistry",
    "EvidenceObservation",
    "EvidenceState",
    "EvidenceStore",
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
    "PackLifecycleState",
    "DriftResult",
    "ProtocolDriftReport",
    "ProtocolProfile",
    "ProtocolRegistry",
    "RetailActivationBlocked",
    "RetailJourneyState",
    "RetailOrder",
    "RetailProduct",
    "RetailQuote",
    "RetailReferenceEnvironment",
    "RetailResult",
    "RetailVariant",
    "PackEvalHarness",
    "PackRegistry",
    "PackResourceLimitError",
    "TraceabilityError",
    "TraceabilityRecord",
    "load_builtin_packs",
    "validate_traceability",
]

# ADR-025: Sector-pack ABI and lifecycle

Status: accepted for Phase 3 builder implementation.

Sector packs are validated declarative bundles with a deterministic `sector.*` namespace, canonical content hash, core compatibility range, explicit lifecycle state, and declared dependencies. The registry owns lifecycle transitions and keeps pack disablement separate from core behavior. Invalid transitions and incompatible activation fail closed.

The ABI is intentionally narrower than arbitrary Python plugins: pack data compiles into canonical v2 models; packs cannot monkey-patch core services or install hidden runtime hooks.


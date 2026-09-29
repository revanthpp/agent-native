# ADR-011: v2 behavior lives in canonical root modules

## Decision

The active v2 implementation is under `src/agentnative/`. `V2/` is reserved
for BRD, prompt, QA, and historical handoff documents. Protocol models and
adapters, capability normalization, identity/signature/replay, delegation,
ownership, policy, and mutation seams each have an owning root package.

The former duplicate `v2core.py` concentration and incubation runtime are not
part of the product package. Compatibility entry points may re-export a
canonical API, but they do not own implementation logic.

## Consequences

- Traceability can point to one real production path and one root test suite.
- Building a wheel cannot accidentally publish the incubation namespace.
- Phase gates remain independent of the historical prompt archive.
- The v2 build shares only explicitly promoted v1 boundaries, such as safe
  acquisition and secret-safe output.

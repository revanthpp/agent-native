# ADR-023: Dry-Run Plan Boundary

## Status

Accepted for Phase 2C.

## Decision

Dry-run calls only an adapter's explicitly non-mutating `build_plan()` method.
It never calls active `prepare()` or remote `preview()`. Adapters without a
local plan return a local plan and the limitation
`REMOTE_PREVIEW_NOT_EXECUTED_IN_DRY_RUN`. Adapter-visible snapshots are
compared around planning and any change fails closed as
`DRY_RUN_SIDE_EFFECT`.

## Consequences

Dry-run reports what Agent Native would attempt without fabricating remote
transaction facts. Adapter construction remains outside the simulator and is
required to be side-effect free by the adapter contract.

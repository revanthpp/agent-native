# ADR-013: Preview and Commit Separation

Status: Accepted

Execution adapters must expose `prepare`, `preview`, `execute`, `verify`, and
`compensate`. A missing preview is a limitation/failure; the simulator never
fabricates preview semantics.

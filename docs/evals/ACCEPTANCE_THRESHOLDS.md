# Acceptance Thresholds

## v0.1 initial gates

- 100% of controlled deterministic fixture expectations pass.
- 100% of PASS, FAIL, and WARN results contain at least one valid evidence item.
- 100% of semantic snapshot comparisons are stable for static fixtures.
- 0 successful private, loopback, link-local, reserved, multicast, or metadata-style network fetches in the security suite.
- 0 target JavaScript executions or side-effectful API invocations.
- malformed input never crashes the entire scan process.
- terminal and JSON outputs represent the same underlying statuses and check IDs.

The repository is not release-ready when a release-blocking security or evidence gate fails, even if ordinary unit tests are green.

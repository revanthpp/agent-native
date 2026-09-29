# Phase 2B Results

## Passed

- Ownership, identity, delegation, policy, signature/replay, DPoP, and policy-store tests pass in the root suite.
- Ed25519 signature verification passed for an unseen signed request.
- Modified method invalidated the signature.
- Duplicate nonce replay was rejected.
- Invalid integrity cannot be promoted to `CRYPTOGRAPHICALLY_VERIFIED`.
- Delegation confused-deputy cases denied wrong principal, wrong agent, wrong capability, wrong resource, and excessive value.
- State-changing authorization fails closed when policy is missing.
- Mutation script reports 17/17 caught against production controls.

## Residual

- OAuth remains partly evidence/assessment oriented rather than a complete runtime OAuth conformance matrix, matching traceability `PARTIAL`.
- Phase 2B should remain conditional until Phase 2A clears its open direct-parser finding and the independent audit is accepted.

## Verdict

`PHASE_2B_CONDITIONALLY_READY`.

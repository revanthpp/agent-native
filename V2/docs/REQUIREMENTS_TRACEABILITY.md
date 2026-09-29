# v2 Requirements Traceability (historical incubation record)

> This file is retained with the prompt/BRD archive and is not a release
> source of truth. The canonical, QA-remediated traceability table is
> [`docs/REQUIREMENTS_TRACEABILITY.md`](../../docs/REQUIREMENTS_TRACEABILITY.md).

The paths and statuses below describe the pre-migration incubation snapshot.

Phase 2A is the current implementation scope. Requirements outside Phase 2A are designed by the BRD but intentionally remain `NOT_STARTED` until their phase gate.

| Requirements | Component / module | Tests/evals | Gate | Status |
|---|---|---|---|---|
| V2-PROT-001..004 | `protocols/base.py`, `protocols/registry.py` | `tests/protocols/test_adapters.py` | 2A | IMPLEMENTED |
| V2-OAS-001..005 | `protocols/openapi/adapter.py` | `tests/protocols/test_openapi.py`, adversarial refs | 2A | IMPLEMENTED |
| V2-MCP-001..007 | `protocols/mcp/adapter.py` | `tests/protocols/test_mcp.py` | 2A | IMPLEMENTED |
| V2-A2A-001..006 | `protocols/a2a/adapter.py` | `tests/protocols/test_a2a.py` | 2A | IMPLEMENTED |
| V2-CAP-001..004 | `capabilities/normalize.py`, `core/types.py` | `tests/unit/test_capabilities.py` | 2A | IMPLEMENTED |
| V2-OWN-001..005 | future ownership module | future ownership evals | 2B | NOT_STARTED |
| V2-ID-001..005 | future identity module | future identity evals | 2B | NOT_STARTED |
| V2-AUTH-001..008 | future delegation module | future auth evals | 2B | NOT_STARTED |
| V2-POL-001..008 | future policy module | future policy evals | 2B | NOT_STARTED |
| V2-SIM-001..009 | future simulator | future simulator evals | 2C | NOT_STARTED |
| V2-TXN-001..007 | future transaction engine | future transaction evals | 2C | NOT_STARTED |
| V2-REC-001..005 | future receipt engine | future receipt evals | 2C | NOT_STARTED |
| V2-OBS-001..005 | future observability module | future observability evals | 2D | NOT_STARTED |
| V2-GW-001..006 | future edge/gateway | future gateway evals | 2D | NOT_STARTED |
| V2-REP-001..004 | future report generator | future report evals | 2D | NOT_STARTED |
| V2-GOV-001..007 | future governance artifacts | future governance evals | final | NOT_STARTED |

## Phase 2B detail

| Requirement IDs | Implementation | Tests | Status |
|---|---|---|---|
| V2-OWN-001..005 | `ownership.py` | `test_ownership.py` | IMPLEMENTED |
| V2-ID-001..002, V2-ID-005 | `identity.py` | `test_identity_delegation_policy.py` | IMPLEMENTED |
| V2-AUTH-002..003, V2-AUTH-005..008 | `delegation.py` | `test_identity_delegation_policy.py` | IMPLEMENTED |
| V2-POL-001..006, V2-POL-008 | `policy.py` | `test_identity_delegation_policy.py` | IMPLEMENTED |
| V2-ID-003..004, V2-AUTH-001, V2-AUTH-004, V2-POL-007 | future signature/OAuth/edge integration | future adversarial/mutation evals | NOT_STARTED |
| V2-ID-003..004 | `request_integrity.py`, `identity.py` | `test_integrity_policy_audit.py` | IMPLEMENTED |
| V2-AUTH-001, V2-AUTH-004 | `oauth.py` evidence assessment | `test_integrity_policy_audit.py` | DESIGNED |
| V2-POL-004..006 | `policy.py`, `policy_store.py` | policy determinism/audit tests | IMPLEMENTED |
| V2-ID-003..004, V2-AUTH-004 | `src/agentnative/v2core.py` request/DPoP verification | `tests/unit/test_v2_canonical.py`, mutation run | VERIFIED |
| V2-POL-002, V2-POL-004..006 | `authorize_state_change`, `PolicyEngine`, `VersionedPolicyStore` | fail-closed matrix, audit/version tests | VERIFIED |
| Phase 2B closure controls | root package, package verifier, mutation script | wheel inspection, `run_phase2b_mutations.py` | VERIFIED |

The grouped ranges above enumerate every normative BRD requirement ID; the source BRD remains authoritative for each individual acceptance criterion.

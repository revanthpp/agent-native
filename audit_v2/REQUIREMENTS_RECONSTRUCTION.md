# Requirements Reconstruction

## Phase 2A Mandatory

- V2-PROT-001..004: common protocol adapter contract, versioned behavior, isolation, extension adapter path.
- V2-OAS-001..005: safe YAML OpenAPI, version declaration, bounded safe `$ref`, structural validity, operation normalization.
- V2-MCP-001..007: passive MCP surface discovery/inventory, schema/contract analysis, contradiction detection, auth findings, unknown-extension safety.
- V2-A2A-001,002,005,006: Agent Card validation, skill normalization, auth declaration, trust boundary.
- V2-CAP-001..004: canonical capability model, action classes, monotonic risk, evidence-backed derivation.

## Phase 2A Partial/Deferred

- A2A task lifecycle and streaming remain partial/passive in this remediation and are not full active protocol behavior.

## Phase 2B Mandatory

- V2-OWN-001..005: ownership gate, DNS/HTTPS methods, environment classification, expiry, target binding.
- V2-ID-001..005: identity model, identity != authorization, signed request support, replay defense, unknown-agent semantics.
- V2-AUTH-001..008: OAuth evidence baseline, least/excess privilege, DPoP/sender constraint where possible, expiry/revocation/principal/resource/audience binding.
- V2-POL-001..008: policy object, default deny, explicit read policy, determinism, explainability, linting, non-bypass, simulation without execution.

## Traceability Comparison

Root `docs/REQUIREMENTS_TRACEABILITY.md` is materially improved and maps to canonical root files. It correctly marks OAuth and adapter non-bypass as partial. Historical `V2/docs/REQUIREMENTS_TRACEABILITY.md` still contains stale `v2core` references and should not be used as release evidence.

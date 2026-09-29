# v1 to v2 Component Matrix

| Component | Decision | Rationale |
|---|---|---|
| SafeFetcher / NetworkPolicy | REUSE | Existing SSRF, redirect, and bounded-acquisition controls remain authoritative. |
| Sanitizer / secret detection | REUSE | Preserve proven public-output boundary. |
| Evidence / public report | WRAP | v2 adds protocol, policy, and receipt references. |
| OpenAPI parser | REPLACE | v2 needs YAML, pinned versions, and bounded refs; v1 behavior remains regression-tested. |
| Check catalog / engine | KEEP | Passive v1 checks stay available through `scan`. |
| CLI | MERGE | Keep `scan`, add v2 protocol/owner/policy commands. |
| CI | MERGE | Add clean v2 install and Phase 2A/2B suites without reducing v1 coverage. |
| Fixtures / evals | MERGE | Preserve v1 corpus and add v2 protocol/security fixtures. |
| Threat model / governance | WRAP | Add v2 ownership, identity, delegation, and policy threats. |
| Temporary `v2/` implementation tree | REMOVE_AFTER_MIGRATION | Avoid two active product source trees after root verification. |

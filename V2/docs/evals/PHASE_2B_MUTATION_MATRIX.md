# Phase 2B Mutation Matrix — QA remediation

The earlier `16/16 caught` result is retired as release evidence because the
old runner compared identical toy lambdas. The current runner injects one
disabled control into canonical production APIs and evaluates the same
adversarial scenario before and after the mutation.

Run:

```bash
PYTHONPATH=src python scripts/run_phase2b_mutations.py
```

Current local result: 17/17 mutations caught. This is builder-run evidence,
not the independent `audit_v2/` evidence required for a release decision.

| Mutation IDs | Production seam | Invariant |
|---|---|---|
| M-OWNERSHIP, M-SIGNATURE, M-REPLAY | `policy/authorization.py` | owner, signature, and replay gates fail closed |
| M-GRANT-EXPIRY, M-REVOCATION, M-PRINCIPAL, M-AGENT, M-PROVIDER, M-AUDIENCE, M-CAPABILITY, M-RESOURCE, M-VALUE | `delegation/models.py` | delegation constraints cannot be bypassed |
| M-DENY, M-DEFAULT, M-VERSION | `policy/engine.py` | deny precedence, default deny, and policy-version binding remain enforced |
| M-REDACTION | `security/sanitize.py` | detected secrets never reach output |
| M-REF-NETWORK | `protocols/openapi/refs.py` | unsafe remote references are blocked before fetch |

The runner never rewrites source files. A surviving mutation exits nonzero.

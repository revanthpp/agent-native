# Known Limitations

- v0.1 supports JSON OpenAPI deterministically; YAML and `$ref` resolution are deferred.
- Passive metadata cannot prove runtime authorization, token validation, object-level access control, idempotency, rollback, or side-effect behavior.
- MCP and A2A are reserved as adapters but do not yet have conformance clients.
- Secret detection is pattern-based and cannot guarantee that every secret form is found.
- Public HTTPS hostname validation depends on the host resolver and must be paired with a dedicated egress policy in hosted deployments.
- The report is a readiness profile, not a certification, legal conclusion, security guarantee, or global score.

# ADR-033: Tenant- and environment-bound connectors

Status: Accepted for RC1 implementation

Connector bindings carry tenant, business, environment, endpoint allowlist, credential reference/class, permitted capabilities, and side-effect mode. Endpoint policy rejects credential-bearing URLs, environment mismatches, forbidden schemes, unallowlisted hosts, and mutations from read-only or simulated connectors.

The synthetic merchant connector is deterministic and local. It exists to exercise the same boundary contract without real credentials or network access.

# ADR-012: Environment Risk Ceilings

Status: Accepted

Risk ceilings are defined per `SANDBOX`, `STAGING`, `PRODUCTION_READ_ONLY`,
and `PRODUCTION_ACTIVE`. Production-active state-changing simulation is off by
default. Action class and value are checked before policy evaluation and again
before commit.

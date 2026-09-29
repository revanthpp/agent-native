# Simulation Environments

Phase 2C labels every run as `SANDBOX`, `STAGING`, `PRODUCTION_READ_ONLY`, or
`PRODUCTION_ACTIVE`.

- `SANDBOX`: default synthetic active testing with configured ceilings.
- `STAGING`: controlled active testing with value/action ceilings.
- `PRODUCTION_READ_ONLY`: read, recommendation, and preview only.
- `PRODUCTION_ACTIVE`: state-changing simulation disabled by default and not
  enabled by the reference CLI.

Active runs require valid ownership evidence whose environment matches the
scenario. Dedicated test identities and test principals are required. An
environment label is evidence context, not a certification claim.

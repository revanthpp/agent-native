# ADR-021: Exact Monetary Risk Values

## Status

Accepted for Phase 2C.

## Decision

Risk-protected amounts use a bounded `Decimal`-backed `MonetaryValue`. Inputs
must be finite, non-negative, numeric (but not boolean), and accompanied by a
supported currency. Currency is trimmed and uppercased; no FX conversion is
performed. A value is allowed at the inclusive ceiling and denied above it.

## Consequences

Malformed values, missing or mismatched currencies, and unsupported currencies
fail closed before authorization and quote creation. The reference currency
catalog and maximum amount are intentionally bounded; adding currencies
requires an explicit code and test update.

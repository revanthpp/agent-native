# Confirmation Results

Result: pass.

Independent checks:

- missing required confirmation returned `AWAITING_CONFIRMATION`;
- wrong principal returned `FAILED` with `CONFIRMATION_CONTEXT_MISMATCH`;
- valid confirmation executed;
- replay returned `FAILED` with `CONFIRMATION_REPLAY`;
- expired confirmation returned `FAILED` with `CONFIRMATION_OR_QUOTE_EXPIRED`.

Shipped mutations:

- `M2C-CONFIRMATION`
- `M2C-CONFIRMATION-BINDING`
- `M2C-CONFIRMATION-REPLAY`
- `M2C-QUOTE-EXPIRY`

All were caught.

# ADR-034: Separate Retail payment, return, and refund authority

Status: Accepted for RC1 implementation

Purchase, payment authorization, return request/approval/receipt, and refund execution use separate capabilities and idempotency identities. Payment authorization is represented without card data and is not merchant acceptance. Refund execution requires a separately authorized payment and enforces the remaining refundable ceiling.

Unknown refund outcomes create reconciliation work rather than triggering an unverified retry. Purchase receipts and refund receipts remain distinct and independently verifiable.

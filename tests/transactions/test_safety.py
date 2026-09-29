import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from agentnative.ownership.models import Environment
from agentnative.protocols.models import ActionClass
from agentnative.transactions import Confirmation, MonetaryValue, Quote, TransactionSafetyEngine, TransactionSafetyError, default_risk_ceiling


class TransactionSafetyTests(unittest.TestCase):
    def setUp(self):
        self.engine = TransactionSafetyEngine()
        self.quote = Quote.create(capability_id="cap", resource_reference="resource", value=10, currency="USD", terms={}, version="1", principal_reference="principal", business_id="business", environment=Environment.SANDBOX, now=datetime.now(timezone.utc))

    def test_quote_expiry_and_context_are_enforced(self):
        with self.assertRaises(TransactionSafetyError) as raised:
            self.engine.check_quote(self.quote, capability_id="cap", resource_reference="resource", value=10, currency="USD", principal_reference="principal", business_id="business", environment=Environment.SANDBOX, resource_version="2")
        self.assertEqual(raised.exception.code, "TOCTOU_RESOURCE_CHANGED")
        expired = Quote.create(capability_id="cap", resource_reference="resource", value=10, currency="USD", terms={}, version="1", principal_reference="principal", business_id="business", environment=Environment.SANDBOX, ttl=timedelta(seconds=-1))
        with self.assertRaises(TransactionSafetyError) as raised:
            self.engine.check_quote(expired, capability_id="cap", resource_reference="resource", value=10, currency="USD", principal_reference="principal", business_id="business", environment=Environment.SANDBOX, resource_version="1")
        self.assertEqual(raised.exception.code, "QUOTE_EXPIRED")

    def test_confirmation_binds_to_quote_and_is_single_use(self):
        confirmation = Confirmation.create(self.quote)
        self.engine.consume_confirmation(confirmation, self.quote, principal_reference="principal")
        with self.assertRaises(TransactionSafetyError) as raised:
            self.engine.consume_confirmation(confirmation, self.quote, principal_reference="principal")
        self.assertEqual(raised.exception.code, "CONFIRMATION_REPLAY")

    def test_idempotency_key_cannot_change_request(self):
        self.engine.record_idempotency("key", "hash-a", "SUCCESS", "result")
        with self.assertRaises(TransactionSafetyError) as raised:
            self.engine.claim_idempotency("key", "hash-b")
        self.assertEqual(raised.exception.code, "IDEMPOTENCY_KEY_REUSE")

    def test_monetary_value_validation_is_exact_and_fail_closed(self):
        ceiling = default_risk_ceiling(Environment.SANDBOX)
        allowed = [(Decimal("0"), "USD"), (Decimal("0.01"), "USD"), (Decimal("99.99"), "USD"), (Decimal("100.00"), "usd")]
        for amount, currency in allowed:
            self.assertEqual(ceiling.allows(ActionClass.CREATE, amount, currency)[0], True)
        for amount, currency, code in [
            (Decimal("100.01"), "USD", "RISK_CEILING_EXCEEDED"),
            (-1, "USD", "RISK_VALUE_NEGATIVE"),
            (float("nan"), "USD", "RISK_VALUE_NON_FINITE"),
            (float("inf"), "USD", "RISK_VALUE_NON_FINITE"),
            (float("-inf"), "USD", "RISK_VALUE_NON_FINITE"),
            (Decimal("1e30"), "USD", "RISK_VALUE_OUT_OF_RANGE"),
            ("100", "USD", "RISK_VALUE_INVALID"),
            (True, "USD", "RISK_VALUE_INVALID"),
            (None, "USD", "RISK_VALUE_REQUIRED"),
            (10, None, "RISK_CURRENCY_REQUIRED"),
            (10, "EUR", "RISK_CURRENCY_MISMATCH"),
            (10, "BTC", "RISK_CURRENCY_UNSUPPORTED"),
        ]:
            self.assertEqual(ceiling.allows(ActionClass.CREATE, amount, currency), (False, code))
        self.assertEqual(MonetaryValue.parse(Decimal("10.00"), " usd ")[0].currency, "USD")

    def test_atomic_idempotency_claim_reserves_before_completion(self):
        self.assertIsNone(self.engine.claim_idempotency("key", "hash-a"))
        record = self.engine.idempotency["key"]
        self.assertEqual(record.status, "PENDING")
        self.engine.record_idempotency("key", "hash-a", "SUCCEEDED", "result")
        self.assertEqual(self.engine.claim_idempotency("key", "hash-a").result_reference, "result")


if __name__ == "__main__":
    unittest.main()

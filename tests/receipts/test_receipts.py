import unittest

from agentnative.receipts import ReceiptEngine


class ReceiptTests(unittest.TestCase):
    def _receipt(self, **overrides):
        values = {
            "business_id": "business",
            "environment": "SANDBOX",
            "agent_id": "agent",
            "provider_id": "provider",
            "principal_reference": "principal",
            "capability_id": "capability",
            "policy_id": "policy",
            "policy_version": "1",
            "decision": "ALLOW",
            "delegation_reference": "grant",
            "confirmation_reference": None,
            "quote_reference": "quote",
            "request_hash": "a" * 64,
            "result": "EXECUTED",
            "side_effect": "REVERSIBLE",
            "resource_reference": "resource",
            "value": 10,
            "currency": "USD",
            "correlation_id": "correlation",
            "trace_id": "trace",
            "evidence_refs": ("policy_decided",),
        }
        values.update(overrides)
        return ReceiptEngine().create(**values)

    def test_receipt_integrity_round_trip_and_modification_detection(self):
        engine = ReceiptEngine()
        receipt = self._receipt()
        self.assertEqual(engine.verify(receipt).status, "VALID")
        modified = {**receipt.to_dict(), "value": 1000}
        self.assertEqual(engine.verify(modified).status, "INVALID")

    def test_receipt_minimizes_sensitive_references_before_hashing(self):
        receipt = self._receipt(principal_reference="token=SECRET_TOKEN_1234567890")
        rendered = receipt.to_dict()
        self.assertNotIn("SECRET_TOKEN_1234567890", repr(rendered))
        self.assertEqual(ReceiptEngine().verify(receipt).status, "VALID")


if __name__ == "__main__":
    unittest.main()

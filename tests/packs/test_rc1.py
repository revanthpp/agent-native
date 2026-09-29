import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from agentnative.connectors import ConnectorBinding, ConnectorEnvironmentPolicy, ConnectorPolicyError, SideEffectMode
from agentnative.packs import (
    AttestationSubject,
    AttestedGuarantee,
    CoreGuaranteeAttestation,
    CoreGuaranteeRegistry,
    CoreTrustStore,
    DependencyLock,
    PackSignatureVerifier,
    PackSigner,
    PackTrustPolicy,
    RetailJourneyState,
    RetailProduct,
    RetailReferenceEnvironment,
    RetailVariant,
    TrustedAttestationKey,
    load_builtin_packs,
)
from agentnative.persistence import SQLiteStateStore
from agentnative.receipts import ReceiptEngine
from agentnative.ownership import Environment


REQUIRED = ("identity_binding_v1", "delegation_scope_v1", "transaction_identity_v1", "replay_safe_confirmation_v1", "idempotency_atomicity_v1", "receipt_integrity_v1")


class RC1HardeningTests(unittest.TestCase):
    def test_signed_core_attestation_is_subject_bound_and_revocable(self):
        private = Ed25519PrivateKey.generate()
        subject = AttestationSubject("github.com/revanthpp/agent-native", "commit-rc1", "2.0.0a1", "core-hash")
        now = datetime.now(timezone.utc)
        attestation = CoreGuaranteeAttestation("audit-rc1", "1.0", subject, tuple(AttestedGuarantee(item, "VERIFIED", (f"evidence:{item}",)) for item in REQUIRED), "run-rc1", "independent-reviewer", now.isoformat(), (now + timedelta(days=30)).isoformat(), key_id="audit-key").sign(private)
        trust = CoreTrustStore([TrustedAttestationKey("audit-key", private.public_key(), environment="SANDBOX")])
        registry = CoreGuaranteeRegistry.from_attestation(attestation, trust, expected_subject=subject, required=REQUIRED)
        registry.require(REQUIRED)
        trust.revoke_attestation(attestation.attestation_id)
        with self.assertRaises(Exception):
            CoreGuaranteeRegistry.from_attestation(attestation, trust, expected_subject=subject, required=REQUIRED)

    def test_signed_pack_requires_trusted_key_and_dependency_lock(self):
        pack = load_builtin_packs().get("sector.retail")
        private = Ed25519PrivateKey.generate()
        lock = DependencyLock(({"name": "connector.retail.reference", "version": "1.0.0", "hash": "sha256:fixture"},))
        envelope = PackSigner().sign(pack, private, key_id="pack-key", dependency_lock=lock, publisher="agentnative")
        policy = PackTrustPolicy(environment="SANDBOX", trusted_key_ids=("pack-key",), trusted_publishers=("agentnative",))
        PackSignatureVerifier().verify(pack, envelope, public_keys={"pack-key": private.public_key()}, policy=policy, dependency_lock=lock)
        with self.assertRaises(Exception):
            PackSignatureVerifier().verify(pack, envelope, public_keys={"pack-key": private.public_key()}, policy=policy, dependency_lock=DependencyLock())

    def test_sqlite_restart_replays_order_and_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = SQLiteStateStore(Path(directory) / "state.db")
            kwargs = {"business_id": "merchant:rc1", "core_guarantees": CoreGuaranteeRegistry.for_test(), "storage": storage}
            first = RetailReferenceEnvironment(**kwargs)
            first.add_product(RetailProduct("prod:shoe", "Shoe", {"variant:red-9": RetailVariant("variant:red-9", {}, 49.99, "USD", 1)}))
            quote = first.create_quote(product_id="prod:shoe", variant_id="variant:red-9", principal_id="principal:test")
            from agentnative.transactions import Confirmation
            confirmation = Confirmation.create(quote.quote)
            accepted = first.submit_order(retail_quote=quote, principal_id="principal:test", agent_id="agent:test", provider_id="provider:test", trust_class="VERIFIED", idempotency_key="restart-key", confirmation=confirmation)
            second = RetailReferenceEnvironment(**kwargs)
            replay = second.submit_order(retail_quote=quote, principal_id="principal:test", agent_id="agent:test", provider_id="provider:test", trust_class="VERIFIED", idempotency_key="restart-key", confirmation=confirmation)
            self.assertEqual(replay.status, "REPLAYED")
            self.assertEqual(replay.order.order_id, accepted.order.order_id)
            self.assertEqual(ReceiptEngine().verify(replay.receipt).status, "VALID")

    def test_retail_payment_return_refund_are_separate_identities(self):
        env = RetailReferenceEnvironment(business_id="merchant:rc1", core_guarantees=CoreGuaranteeRegistry.for_test())
        env.add_product(RetailProduct("prod:item", "Item", {"variant:one": RetailVariant("variant:one", {}, 10.0, "USD", 1)}))
        quote = env.create_quote(product_id="prod:item", variant_id="variant:one", principal_id="principal:test")
        from agentnative.transactions import Confirmation
        order_result = env.submit_order(retail_quote=quote, principal_id="principal:test", agent_id="agent:test", provider_id="provider:test", trust_class="VERIFIED", idempotency_key="buy-key", confirmation=Confirmation.create(quote.quote))
        payment = env.authorize_payment(order_id=order_result.order.order_id, principal_id="principal:test", idempotency_key="payment-key")
        self.assertEqual(payment.state.value, "AUTHORIZED")
        order_result.order.state = RetailJourneyState.FULFILLED
        return_request = env.create_return_request(order_id=order_result.order.order_id, principal_id="principal:test", reason="wrong size", idempotency_key="return-key")
        env.approve_return(return_request.return_id)
        env.receive_return(return_request.return_id)
        refund_request = env.request_refund(return_id=return_request.return_id, principal_id="principal:test", idempotency_key="refund-request-key")
        refund = env.execute_refund(refund_id=refund_request.refund_id, principal_id="principal:test", idempotency_key="refund-key")
        replay = env.execute_refund(refund_id=refund_request.refund_id, principal_id="principal:test", idempotency_key="refund-key")
        self.assertEqual(refund.state, RetailJourneyState.REFUNDED)
        self.assertEqual(replay.refund_id, refund.refund_id)
        with self.assertRaises(Exception):
            env.execute_refund(refund_id=refund_request.refund_id, principal_id="principal:test", idempotency_key="refund-new", amount=20.0)

    def test_connector_policy_rejects_boundary_crossing(self):
        policy = ConnectorEnvironmentPolicy()
        sandbox = ConnectorBinding("retail", "1.0", "tenant:a", "merchant:a", "SANDBOX", ("sandbox.merchant.test",), "cred:sandbox", "sandbox", ("read",), SideEffectMode.SANDBOX_MUTATION)
        policy.validate(sandbox, endpoint="https://sandbox.merchant.test:443", transaction_environment="SANDBOX", mutation=True)
        with self.assertRaises(ConnectorPolicyError):
            policy.validate(sandbox, endpoint="https://prod.merchant.test:443", transaction_environment="SANDBOX", mutation=True)
        with self.assertRaises(ConnectorPolicyError):
            policy.validate(sandbox, endpoint="http://127.0.0.1:8080", transaction_environment="SANDBOX", mutation=True)

    def test_test_fixture_cannot_activate_retail_in_production(self):
        with self.assertRaises(Exception):
            RetailReferenceEnvironment(business_id="merchant:prod", environment=Environment.PRODUCTION_ACTIVE, core_guarantees=CoreGuaranteeRegistry.for_test())


if __name__ == "__main__":
    unittest.main()

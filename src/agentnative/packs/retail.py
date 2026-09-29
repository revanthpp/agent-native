from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

from agentnative.observability import TraceContext, TraceRecorder
from agentnative.ownership import Environment
from agentnative.packs.core_gates import CoreGuaranteeError, CoreGuaranteeRegistry
from agentnative.persistence import SQLiteStateStore
from agentnative.receipts import Receipt, ReceiptEngine
from agentnative.transactions import Confirmation, Quote, TransactionSafetyEngine, TransactionSafetyError
from agentnative.transactions.core import stable_hash


class RetailJourneyState(StrEnum):
    DISCOVERED = "DISCOVERED"
    QUOTED = "QUOTED"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    CONFIRMED = "CONFIRMED"
    SUBMISSION_PENDING = "SUBMISSION_PENDING"
    ORDER_ACCEPTED = "ORDER_ACCEPTED"
    ORDER_REJECTED = "ORDER_REJECTED"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCELLED = "CANCELLED"
    RETURN_ELIGIBLE = "RETURN_ELIGIBLE"
    RETURN_INELIGIBLE = "RETURN_INELIGIBLE"
    REFUND_PENDING = "REFUND_PENDING"
    REFUNDED = "REFUNDED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    MANUAL_ESCALATION = "MANUAL_ESCALATION"
    RETURN_NOT_REQUESTED = "RETURN_NOT_REQUESTED"
    RETURN_REQUESTED = "RETURN_REQUESTED"
    RETURN_AUTHORIZED = "RETURN_AUTHORIZED"
    RETURN_REJECTED = "RETURN_REJECTED"
    RETURN_IN_TRANSIT = "RETURN_IN_TRANSIT"
    RETURN_RECEIVED = "RETURN_RECEIVED"
    RETURN_INSPECTION_REQUIRED = "RETURN_INSPECTION_REQUIRED"
    RETURN_COMPLETED = "RETURN_COMPLETED"
    REFUND_NOT_REQUESTED = "REFUND_NOT_REQUESTED"
    REFUND_AUTHORIZATION_PENDING = "REFUND_AUTHORIZATION_PENDING"
    REFUND_AUTHORIZED = "REFUND_AUTHORIZED"
    REFUND_REJECTED = "REFUND_REJECTED"
    REFUND_SUBMITTED = "REFUND_SUBMITTED"
    REFUND_FAILED = "REFUND_FAILED"
    REFUND_UNKNOWN_OUTCOME = "REFUND_UNKNOWN_OUTCOME"
    REFUND_RECONCILIATION_REQUIRED = "REFUND_RECONCILIATION_REQUIRED"


class PaymentAuthorizationState(StrEnum):
    AUTHORIZED = "AUTHORIZED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    REQUIRES_ACTION = "REQUIRES_ACTION"
    TIMEOUT_UNKNOWN = "TIMEOUT_UNKNOWN"
    CONNECTOR_UNAVAILABLE = "CONNECTOR_UNAVAILABLE"
    REVERSED = "REVERSED"


@dataclass
class RetailVariant:
    variant_id: str
    options: dict[str, str]
    price: float
    currency: str
    inventory: int
    version: str = "1"


@dataclass
class RetailProduct:
    product_id: str
    title: str
    variants: dict[str, RetailVariant]


@dataclass(frozen=True)
class RetailQuote:
    quote: Quote
    state: RetailJourneyState
    product_id: str
    variant_id: str
    terms: dict[str, Any]


@dataclass
class RetailOrder:
    order_id: str
    product_id: str
    variant_id: str
    principal_id: str
    amount: float
    currency: str
    state: RetailJourneyState = RetailJourneyState.ORDER_ACCEPTED
    quantity: int = 1
    trace_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"order_id": self.order_id, "product_id": self.product_id, "variant_id": self.variant_id, "principal_id": self.principal_id, "amount": self.amount, "currency": self.currency, "state": self.state.value, "quantity": self.quantity, "trace_id": self.trace_id}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RetailOrder":
        return cls(str(raw["order_id"]), str(raw["product_id"]), str(raw["variant_id"]), str(raw["principal_id"]), float(raw["amount"]), str(raw["currency"]), RetailJourneyState(str(raw["state"])), int(raw.get("quantity", 1)), str(raw.get("trace_id", "")))


@dataclass(frozen=True)
class PaymentAuthorization:
    authorization_id: str
    order_id: str
    amount: float
    currency: str
    state: PaymentAuthorizationState
    idempotency_key: str

    def to_dict(self) -> dict[str, Any]:
        return {"authorization_id": self.authorization_id, "order_id": self.order_id, "amount": self.amount, "currency": self.currency, "state": self.state.value, "idempotency_key": self.idempotency_key}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PaymentAuthorization":
        return cls(str(raw["authorization_id"]), str(raw["order_id"]), float(raw["amount"]), str(raw["currency"]), PaymentAuthorizationState(str(raw["state"])), str(raw["idempotency_key"]))


@dataclass(frozen=True)
class RetailReturn:
    return_id: str
    order_id: str
    state: RetailJourneyState
    reason: str
    idempotency_key: str

    def to_dict(self) -> dict[str, Any]:
        return {"return_id": self.return_id, "order_id": self.order_id, "state": self.state.value, "reason": self.reason, "idempotency_key": self.idempotency_key}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RetailReturn":
        return cls(str(raw["return_id"]), str(raw["order_id"]), RetailJourneyState(str(raw["state"])), str(raw["reason"]), str(raw["idempotency_key"]))


@dataclass(frozen=True)
class RetailRefund:
    refund_id: str
    order_id: str
    amount: float
    currency: str
    state: RetailJourneyState
    idempotency_key: str
    payment_reference: str
    receipt: Receipt | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"refund_id": self.refund_id, "order_id": self.order_id, "amount": self.amount, "currency": self.currency, "state": self.state.value, "idempotency_key": self.idempotency_key, "payment_reference": self.payment_reference, "receipt": self.receipt.to_dict() if self.receipt else None}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RetailRefund":
        return cls(str(raw["refund_id"]), str(raw["order_id"]), float(raw["amount"]), str(raw["currency"]), RetailJourneyState(str(raw["state"])), str(raw["idempotency_key"]), str(raw["payment_reference"]), Receipt.from_dict(raw["receipt"]) if raw.get("receipt") else None)


@dataclass(frozen=True)
class RetailResult:
    status: str
    state: RetailJourneyState
    message: str
    order: RetailOrder | None = None
    quote: RetailQuote | None = None
    receipt: Receipt | None = None
    trace: dict[str, Any] = field(default_factory=dict)
    findings: tuple[str, ...] = ()
    replayed: bool = False


class RetailActivationBlocked(RuntimeError):
    pass


class RetailReferenceEnvironment:
    """Deterministic commerce environment using the v2 transaction safety engine."""

    def __init__(self, *, business_id: str, environment: Environment = Environment.SANDBOX, core_guarantees: CoreGuaranteeRegistry | None = None, storage: SQLiteStateStore | None = None) -> None:
        self.business_id = business_id
        self.environment = environment
        self.core_guarantees = core_guarantees or CoreGuaranteeRegistry()
        if self.core_guarantees.is_test_fixture and environment in {Environment.STAGING, Environment.PRODUCTION_READ_ONLY, Environment.PRODUCTION_ACTIVE}:
            raise RetailActivationBlocked("test-only core guarantee fixtures cannot activate outside SANDBOX")
        required = ("identity_binding_v1", "delegation_scope_v1", "transaction_identity_v1", "replay_safe_confirmation_v1", "idempotency_atomicity_v1", "receipt_integrity_v1")
        try:
            self.core_guarantees.require(required)
        except CoreGuaranteeError as exc:
            raise RetailActivationBlocked(str(exc)) from exc
        self.products: dict[str, RetailProduct] = {}
        self.orders: dict[str, RetailOrder] = {}
        self.transactions = TransactionSafetyEngine()
        self.receipts = ReceiptEngine()
        self.storage = storage
        self.payments: dict[str, PaymentAuthorization] = {}
        self.returns: dict[str, RetailReturn] = {}
        self.refunds: dict[str, RetailRefund] = {}
        if self.storage:
            self.orders.update({item.order_id: item for item in (RetailOrder.from_dict(raw) for raw in self.storage.load_orders())})
            self.payments.update({item.authorization_id: item for item in (PaymentAuthorization.from_dict(raw) for raw in self.storage.load_entities("payment"))})
            self.returns.update({item.return_id: item for item in (RetailReturn.from_dict(raw) for raw in self.storage.load_entities("return"))})
            self.refunds.update({item.refund_id: item for item in (RetailRefund.from_dict(raw) for raw in self.storage.load_entities("refund"))})

    def add_product(self, product: RetailProduct) -> None:
        if not product.product_id or not product.variants:
            raise ValueError("retail products require a stable ID and at least one variant")
        self.products[product.product_id] = product
        if self.storage:
            for variant in product.variants.values():
                self.storage.seed_inventory(product.product_id, variant.variant_id, variant.inventory, variant.version)

    def discover(self, product_id: str) -> dict[str, Any]:
        product = self.products[product_id]
        return {
            "state": RetailJourneyState.DISCOVERED.value,
            "product_id": product.product_id,
            "title": product.title,
            "variants": [{"variant_id": item.variant_id, "options": dict(item.options), "price": item.price, "currency": item.currency, "inventory": item.inventory, "observed_at": _now()} for item in product.variants.values()],
        }

    def create_quote(self, *, product_id: str, variant_id: str, principal_id: str, quantity: int = 1, shipping: str = "standard", ttl: timedelta = timedelta(minutes=5), now: datetime | None = None) -> RetailQuote:
        if quantity < 1:
            raise ValueError("quantity must be positive")
        product = self.products[product_id]
        variant = product.variants[variant_id]
        if variant.inventory < quantity:
            raise TransactionSafetyError("INVENTORY_UNAVAILABLE", "requested quantity is not currently available")
        total = round(variant.price * quantity, 2)
        observed_at = (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
        terms = {"shipping": shipping, "shipping_cost": 0.0 if shipping == "standard" else 12.0, "tax_status": "simulated", "inventory_observed_at": observed_at, "quantity": quantity}
        quote = Quote.create(capability_id="sector.retail:submit_order", resource_reference=f"{product_id}:{variant_id}", value=total, currency=variant.currency, terms=terms, version=variant.version, principal_reference=principal_id, business_id=self.business_id, environment=self.environment, ttl=ttl, now=now, evidence_refs=(f"product:{product_id}", f"variant:{variant_id}"))
        return RetailQuote(quote, RetailJourneyState.QUOTED, product_id, variant_id, terms)

    def submit_order(self, *, retail_quote: RetailQuote, principal_id: str, agent_id: str, provider_id: str, trust_class: str, idempotency_key: str, confirmation: Confirmation | None = None, require_confirmation: bool = True, shipping_destination_ref: str = "destination:synthetic", failure_after_commit: bool = False, delegation_expires_at: datetime | None = None, now: datetime | None = None) -> RetailResult:
        clock = now or datetime.now(timezone.utc)
        quote = retail_quote.quote
        deterministic_trace_id = "trace-" + stable_hash({"business": self.business_id, "key": idempotency_key})[:24]
        trace = TraceRecorder(TraceContext(deterministic_trace_id, f"retail:{idempotency_key}"))
        findings: list[str] = []
        if trust_class not in {"VERIFIED", "PARTNER", "INTERNAL"}:
            trace.emit("retail_order_denied", {"reason": "unknown_agent"})
            return self._result("DENIED", RetailJourneyState.ORDER_REJECTED, "unknown agent cannot purchase", retail_quote, trace, findings + ["UNKNOWN_AGENT_PURCHASE"])
        if delegation_expires_at is not None and delegation_expires_at <= clock:
            trace.emit("retail_order_denied", {"reason": "expired_delegation"})
            return self._result("DENIED", RetailJourneyState.ORDER_REJECTED, "delegation is expired", retail_quote, trace, findings + ["EXPIRED_DELEGATION"])
        if require_confirmation and confirmation is None:
            trace.emit("confirmation_requested", {"quote_id": quote.quote_id})
            return self._result("CONFIRMATION_REQUIRED", RetailJourneyState.CONFIRMATION_REQUIRED, "confirmation is required before checkout", retail_quote, trace, findings + ["CONFIRMATION_REQUIRED"])
        if retail_quote.terms != quote.terms or not isinstance(retail_quote.terms.get("quantity", 1), int) or int(retail_quote.terms.get("quantity", 1)) < 1:
            trace.emit("retail_order_denied", {"reason": "malformed_request"})
            return self._result("FAILED", RetailJourneyState.ORDER_REJECTED, "quote terms are malformed or do not match the signed quote", retail_quote, trace, findings + ["MALFORMED_REQUEST"])
        capability_id = "sector.retail:submit_order"
        payload = {"product_id": retail_quote.product_id, "variant_id": retail_quote.variant_id, "quantity": quote.terms.get("quantity", 1), "shipping": quote.terms.get("shipping"), "shipping_destination_ref": shipping_destination_ref}
        request_hash = self.transactions.request_hash(capability_id=capability_id, resource_reference=quote.resource_reference, value=quote.value, currency=quote.currency, input_data=payload, business_id=self.business_id, environment=self.environment, principal_id=principal_id, agent_id=agent_id, provider_id=provider_id, quote_id=quote.quote_id, confirmation_id=confirmation.confirmation_id if confirmation else None)
        try:
            existing = self.storage.claim_idempotency(idempotency_key, request_hash, scenario_id="retail.submit_order") if self.storage else self.transactions.claim_idempotency(idempotency_key, request_hash, scenario_id="retail.submit_order")
            if existing is not None:
                if existing.status != "SUCCEEDED":
                    if self.storage:
                        self.storage.add_reconciliation(reconciliation_id="reconcile-" + existing.logical_transaction_id, logical_transaction_id=existing.logical_transaction_id or "", payload={"reason": "pending or ambiguous order after restart", "verification_strategy": "verify_order_by_transaction_identity"})
                    return self._result("UNKNOWN_OUTCOME", RetailJourneyState.RECONCILIATION_REQUIRED, "existing transaction requires reconciliation before retry", retail_quote, trace, findings + ["RECONCILIATION_REQUIRED"])
                order = self.orders.get(existing.result_reference or "")
                stored_receipt = self.storage.get_receipt(idempotency_key, request_hash) if self.storage else self.transactions.get_receipt(idempotency_key, request_hash)
                receipt = Receipt.from_dict(stored_receipt) if isinstance(stored_receipt, dict) else stored_receipt
                trace.emit("result_replayed", {"receipt_reference": getattr(receipt, "receipt_id", None)})
                return self._result("REPLAYED", order.state if order else RetailJourneyState.ORDER_ACCEPTED, "order result replayed", retail_quote, trace, findings, order=order, receipt=receipt, replayed=True)
            product = self.products[retail_quote.product_id]
            variant = product.variants[retail_quote.variant_id]
            TransactionSafetyEngine.check_quote(quote, capability_id=capability_id, resource_reference=quote.resource_reference, value=quote.value, currency=quote.currency, principal_reference=principal_id, business_id=self.business_id, environment=self.environment, resource_version=variant.version, now=clock)
            quantity = int(quote.terms.get("quantity", 1))
            if quantity < 1:
                raise TransactionSafetyError("MALFORMED_REQUEST", "quantity must be positive")
            available_inventory = self.storage.inventory(retail_quote.product_id, retail_quote.variant_id) if self.storage else variant.inventory
            if available_inventory is not None and available_inventory < quantity:
                raise TransactionSafetyError("INVENTORY_UNAVAILABLE", "inventory was lost before checkout")
            logical_id = self.transactions.logical_transaction_id(idempotency_key, request_hash)
            if confirmation is not None:
                self.transactions.consume_confirmation(confirmation, quote, principal_reference=principal_id, logical_transaction_id=logical_id, transaction_fingerprint=request_hash, agent_id=agent_id, provider_id=provider_id, business_id=self.business_id, environment=self.environment, now=clock)
                trace.emit("confirmation_received", {"confirmation_id": confirmation.confirmation_id})
            trace.emit("checkout_submitted", {"logical_transaction_id": logical_id, "quote_id": quote.quote_id})
            order_id = "order-" + stable_hash({"transaction": request_hash, "logical": logical_id})[:24]
            order = RetailOrder(order_id, retail_quote.product_id, retail_quote.variant_id, principal_id, float(quote.value or 0), str(quote.currency), RetailJourneyState.ORDER_ACCEPTED, quantity, trace.context.trace_id)
            receipt = self.receipts.create(business_id=self.business_id, environment=self.environment.value, agent_id=agent_id, provider_id=provider_id, principal_reference=principal_id, capability_id=capability_id, policy_id="retail-reference-policy", policy_version="retail-0.1", decision="ALLOW", delegation_reference="retail-reference-delegation", confirmation_reference=confirmation.confirmation_id if confirmation else None, quote_reference=quote.quote_id, request_hash=request_hash, result="ORDER_ACCEPTED", side_effect="IRREVERSIBLE", resource_reference=quote.resource_reference, value=quote.value, currency=quote.currency, correlation_id=trace.context.correlation_id, trace_id=trace.context.trace_id, evidence_refs=(f"order:{order_id}", f"quote:{quote.quote_id}"), receipt_id="receipt-" + stable_hash({"request": request_hash, "result": "ORDER_ACCEPTED"})[:24], timestamp=clock.isoformat().replace("+00:00", "Z"))
            if self.storage:
                self.storage.commit_order(order=order, key=idempotency_key, request_hash=request_hash, logical_id=logical_id, receipt=receipt, product_id=retail_quote.product_id, variant_id=retail_quote.variant_id, quantity=quantity, business_id=self.business_id, environment=self.environment.value)
                variant.inventory = max(0, variant.inventory - quantity)
                variant.version = str(int(variant.version) + 1)
            else:
                variant.inventory -= quantity
                variant.version = str(int(variant.version) + 1)
                self.transactions.record_idempotency(idempotency_key, request_hash, "SUCCEEDED", order_id, logical_id=logical_id)
                self.transactions.attach_receipt(idempotency_key, request_hash, receipt)
            self.orders[order_id] = order
            trace.emit("order_accepted", {"order_id": order_id})
            if failure_after_commit:
                trace.emit("unknown_outcome", {"order_id": order_id})
                return self._result("UNKNOWN_OUTCOME", RetailJourneyState.UNKNOWN_OUTCOME, "downstream order succeeded but response was lost", retail_quote, trace, findings + ["UNKNOWN_OUTCOME"], order=order, receipt=receipt)
            return self._result("ORDER_ACCEPTED", RetailJourneyState.ORDER_ACCEPTED, "order accepted", retail_quote, trace, findings, order=order, receipt=receipt)
        except TransactionSafetyError as exc:
            findings.append(exc.code)
            if self.storage and exc.code in {"INVENTORY_UNAVAILABLE", "MALFORMED_REQUEST"}:
                self.storage.record_idempotency(idempotency_key, request_hash, "FAILED_TERMINAL", None, error_reference=exc.code)
            trace.emit("retail_order_failed", {"code": exc.code})
            return self._result("FAILED", RetailJourneyState.RECONCILIATION_REQUIRED if exc.state_changed else RetailJourneyState.ORDER_REJECTED, str(exc), retail_quote, trace, findings)

    def cancel_order(self, *, order_id: str, principal_id: str, agent_id: str, provider_id: str, idempotency_key: str) -> RetailResult:
        order = self.orders[order_id]
        if order.principal_id != principal_id:
            return RetailResult("DENIED", RetailJourneyState.ORDER_REJECTED, "principal does not own order", order=order, findings=("PRINCIPAL_MISMATCH",))
        capability_id = "sector.retail:cancel_order"
        request_hash = self.transactions.request_hash(capability_id=capability_id, resource_reference=order_id, value=0, currency="USD", input_data={"order_id": order_id, "operation": "cancel"}, business_id=self.business_id, environment=self.environment, principal_id=principal_id, agent_id=agent_id, provider_id=provider_id)
        existing = self.storage.claim_idempotency(idempotency_key, request_hash, scenario_id="retail.cancel_order") if self.storage else self.transactions.claim_idempotency(idempotency_key, request_hash, scenario_id="retail.cancel_order")
        if existing is not None:
            stored_receipt = self.storage.get_receipt(idempotency_key, request_hash) if self.storage else self.transactions.get_receipt(idempotency_key, request_hash)
            receipt = Receipt.from_dict(stored_receipt) if isinstance(stored_receipt, dict) else stored_receipt
            return RetailResult("REPLAYED", order.state, "cancellation result replayed", order=order, receipt=receipt, replayed=True)
        if order.state not in {RetailJourneyState.ORDER_ACCEPTED, RetailJourneyState.PARTIALLY_FULFILLED}:
            if self.storage:
                self.storage.record_idempotency(idempotency_key, request_hash, "FAILED_TERMINAL", None, error_reference="CANCELLATION_NOT_ALLOWED")
            else:
                self.transactions.record_idempotency(idempotency_key, request_hash, "FAILED_TERMINAL", None, error_reference="CANCELLATION_NOT_ALLOWED")
            return RetailResult("DENIED", order.state, "order is not cancellable", order=order, findings=("CANCELLATION_NOT_ALLOWED",))
        trace = TraceRecorder(TraceContext.new(f"retail:cancel:{idempotency_key}"))
        trace.emit("cancellation_requested", {"order_id": order_id})
        if self.storage and not self.storage.transition_order(order_id, expected_states={RetailJourneyState.ORDER_ACCEPTED.value, RetailJourneyState.PARTIALLY_FULFILLED.value}, new_state=RetailJourneyState.CANCELLED.value):
            self.storage.record_idempotency(idempotency_key, request_hash, "FAILED_TERMINAL", None, error_reference="CANCELLATION_RACE")
            return RetailResult("DENIED", order.state, "order was already transitioned by another execution", order=order, findings=("CANCELLATION_RACE",))
        order.state = RetailJourneyState.CANCELLED
        if self.storage:
            self.storage.record_idempotency(idempotency_key, request_hash, "SUCCEEDED", order_id)
        else:
            self.transactions.record_idempotency(idempotency_key, request_hash, "SUCCEEDED", order_id)
        receipt = self.receipts.create(business_id=self.business_id, environment=self.environment.value, agent_id=agent_id, provider_id=provider_id, principal_reference=principal_id, capability_id=capability_id, policy_id="retail-reference-policy", policy_version="retail-0.1", decision="ALLOW", delegation_reference="retail-reference-delegation", confirmation_reference=None, quote_reference=None, request_hash=request_hash, result="CANCELLED", side_effect="REVERSIBLE", resource_reference=order_id, value=0, currency="USD", correlation_id=trace.context.correlation_id, trace_id=trace.context.trace_id, evidence_refs=(f"order:{order_id}",))
        if self.storage:
            self.storage.attach_receipt(idempotency_key, request_hash, receipt)
            self.storage.save_order(order, event_type="CANCELLED")
        else:
            self.transactions.attach_receipt(idempotency_key, request_hash, receipt)
        trace.emit("cancellation_completed", {"order_id": order_id})
        return RetailResult("CANCELLED", RetailJourneyState.CANCELLED, "order cancelled", order=order, receipt=receipt, trace=trace.export())

    def return_eligibility(self, order_id: str) -> RetailJourneyState:
        order = self.orders[order_id]
        if order.state == RetailJourneyState.FULFILLED:
            order.state = RetailJourneyState.RETURN_ELIGIBLE
            if self.storage:
                self.storage.save_order(order, event_type="RETURN_ELIGIBLE")
        return order.state if order.state in {RetailJourneyState.RETURN_ELIGIBLE, RetailJourneyState.RETURN_INELIGIBLE} else RetailJourneyState.RETURN_INELIGIBLE

    def set_inventory(self, product_id: str, variant_id: str, inventory: int) -> None:
        variant = self.products[product_id].variants[variant_id]
        variant.inventory = inventory
        variant.version = str(int(variant.version) + 1)

    def set_price(self, product_id: str, variant_id: str, price: float) -> None:
        variant = self.products[product_id].variants[variant_id]
        variant.price = price
        variant.version = str(int(variant.version) + 1)

    def authorize_payment(self, *, order_id: str, principal_id: str, idempotency_key: str, outcome: PaymentAuthorizationState = PaymentAuthorizationState.AUTHORIZED, connector_available: bool = True) -> PaymentAuthorization:
        order = self.orders[order_id]
        if order.principal_id != principal_id:
            raise TransactionSafetyError("PRINCIPAL_MISMATCH", "principal does not own order")
        fingerprint = self.transactions.request_hash(capability_id="sector.retail:authorize_payment", resource_reference=order_id, value=order.amount, currency=order.currency, input_data={"order_id": order_id, "amount": order.amount}, business_id=self.business_id, environment=self.environment, principal_id=principal_id, agent_id=None, provider_id=None)
        existing = self.storage.claim_idempotency(idempotency_key, fingerprint, scenario_id="retail.authorize_payment") if self.storage else self.transactions.claim_idempotency(idempotency_key, fingerprint, scenario_id="retail.authorize_payment")
        if existing:
            return self.payments[existing.result_reference or ""]
        authorization_id = "payauth-" + stable_hash({"fingerprint": fingerprint})[:24]
        if not connector_available:
            outcome = PaymentAuthorizationState.CONNECTOR_UNAVAILABLE
        payment = PaymentAuthorization(authorization_id, order_id, order.amount, order.currency, outcome, idempotency_key)
        self.payments[authorization_id] = payment
        if self.storage:
            self.storage.save_entity("payment", payment, entity_id=authorization_id, business_id=self.business_id, environment=self.environment.value)
        status = "SUCCEEDED" if outcome == PaymentAuthorizationState.AUTHORIZED else "UNKNOWN_OUTCOME" if outcome in {PaymentAuthorizationState.TIMEOUT_UNKNOWN, PaymentAuthorizationState.CONNECTOR_UNAVAILABLE} else "FAILED_TERMINAL"
        if self.storage:
            self.storage.record_idempotency(idempotency_key, fingerprint, status, authorization_id)
        else:
            self.transactions.record_idempotency(idempotency_key, fingerprint, status, authorization_id)
        if outcome in {PaymentAuthorizationState.TIMEOUT_UNKNOWN, PaymentAuthorizationState.CONNECTOR_UNAVAILABLE} and self.storage:
            self.storage.add_reconciliation(reconciliation_id="reconcile-" + authorization_id, logical_transaction_id=existing.logical_transaction_id if existing else "tx-" + fingerprint[:24], payload={"downstream_reference": authorization_id, "reason": "payment authorization timeout", "verification_strategy": "get_payment_status"})
        return payment

    def check_return_eligibility(self, *, order_id: str) -> RetailJourneyState:
        return self.return_eligibility(order_id)

    def create_return_request(self, *, order_id: str, principal_id: str, reason: str, idempotency_key: str) -> RetailReturn:
        order = self.orders[order_id]
        if order.principal_id != principal_id:
            raise TransactionSafetyError("PRINCIPAL_MISMATCH", "principal does not own order")
        if self.return_eligibility(order_id) != RetailJourneyState.RETURN_ELIGIBLE:
            raise TransactionSafetyError("RETURN_INELIGIBLE", "order is not eligible for return")
        return_id = "return-" + stable_hash({"order_id": order_id, "key": idempotency_key})[:24]
        result = self.returns.get(return_id) or RetailReturn(return_id, order_id, RetailJourneyState.RETURN_REQUESTED, reason, idempotency_key)
        self.returns[return_id] = result
        if self.storage:
            self.storage.save_entity("return", result, entity_id=return_id, business_id=self.business_id, environment=self.environment.value)
        return result

    def approve_return(self, return_id: str) -> RetailReturn:
        return self._transition_return(return_id, RetailJourneyState.RETURN_AUTHORIZED)

    def receive_return(self, return_id: str, *, inspection_required: bool = False) -> RetailReturn:
        return self._transition_return(return_id, RetailJourneyState.RETURN_INSPECTION_REQUIRED if inspection_required else RetailJourneyState.RETURN_RECEIVED)

    def _transition_return(self, return_id: str, target: RetailJourneyState) -> RetailReturn:
        current = self.returns[return_id]
        allowed = {RetailJourneyState.RETURN_REQUESTED: RetailJourneyState.RETURN_AUTHORIZED, RetailJourneyState.RETURN_AUTHORIZED: RetailJourneyState.RETURN_RECEIVED, RetailJourneyState.RETURN_RECEIVED: RetailJourneyState.RETURN_INSPECTION_REQUIRED}
        if allowed.get(current.state) != target:
            raise TransactionSafetyError("INVALID_RETURN_TRANSITION", f"cannot transition return from {current.state} to {target}")
        updated = RetailReturn(current.return_id, current.order_id, target, current.reason, current.idempotency_key)
        self.returns[return_id] = updated
        if self.storage:
            self.storage.save_entity("return", updated, entity_id=return_id, business_id=self.business_id, environment=self.environment.value)
        return updated

    def request_refund(self, *, return_id: str, principal_id: str, idempotency_key: str) -> RetailRefund:
        return_request = self.returns[return_id]
        order = self.orders[return_request.order_id]
        if order.principal_id != principal_id:
            raise TransactionSafetyError("PRINCIPAL_MISMATCH", "principal does not own order")
        if return_request.state not in {RetailJourneyState.RETURN_RECEIVED, RetailJourneyState.RETURN_INSPECTION_REQUIRED}:
            raise TransactionSafetyError("REFUND_NOT_AUTHORIZED", "return must be received before refund authorization")
        if not any(item.order_id == order.order_id and item.state == PaymentAuthorizationState.AUTHORIZED for item in self.payments.values()):
            raise TransactionSafetyError("PAYMENT_AUTHORIZATION_REQUIRED", "refund authority requires a separate authorized payment")
        refund_id = "refund-" + stable_hash({"order_id": order.order_id, "key": idempotency_key})[:24]
        result = self.refunds.get(refund_id) or RetailRefund(refund_id, order.order_id, order.amount, order.currency, RetailJourneyState.REFUND_AUTHORIZED, idempotency_key, "payment:" + order.order_id)
        self.refunds[refund_id] = result
        if self.storage:
            self.storage.save_entity("refund", result, entity_id=refund_id, business_id=self.business_id, environment=self.environment.value)
        return result

    def execute_refund(self, *, refund_id: str, principal_id: str, idempotency_key: str, amount: float | None = None, failure_after_commit: bool = False) -> RetailRefund:
        requested = self.refunds[refund_id]
        order = self.orders[requested.order_id]
        if order.principal_id != principal_id:
            raise TransactionSafetyError("PRINCIPAL_MISMATCH", "principal does not own order")
        amount = requested.amount if amount is None else round(float(amount), 2)
        prior = sum(item.amount for item in self.refunds.values() if item.order_id == order.order_id and item.state == RetailJourneyState.REFUNDED and item.refund_id != refund_id)
        if amount <= 0 or amount + prior > order.amount:
            raise TransactionSafetyError("REFUND_EXCEEDS_ELIGIBLE_VALUE", "refund amount exceeds the captured value remaining")
        fingerprint = self.transactions.request_hash(capability_id="sector.retail:execute_refund", resource_reference=order.order_id, value=amount, currency=order.currency, input_data={"refund_id": refund_id, "amount": amount, "payment_reference": requested.payment_reference}, business_id=self.business_id, environment=self.environment, principal_id=principal_id, agent_id=None, provider_id=None)
        existing = self.storage.claim_idempotency(idempotency_key, fingerprint, scenario_id="retail.execute_refund") if self.storage else self.transactions.claim_idempotency(idempotency_key, fingerprint, scenario_id="retail.execute_refund")
        if existing:
            return self.refunds[existing.result_reference or refund_id]
        receipt = self.receipts.create(business_id=self.business_id, environment=self.environment.value, agent_id="retail-reference", provider_id="retail-reference", principal_reference=principal_id, capability_id="sector.retail:execute_refund", policy_id="retail-refund-policy", policy_version="retail-0.1", decision="ALLOW", delegation_reference="retail-reference-delegation", confirmation_reference=None, quote_reference=None, request_hash=fingerprint, result="REFUNDED", side_effect="REVERSIBLE", resource_reference=order.order_id, value=amount, currency=order.currency, correlation_id="refund:" + refund_id, trace_id="refund:" + refund_id, evidence_refs=(f"order:{order.order_id}", f"return:{next((key for key, value in self.returns.items() if value.order_id == order.order_id), '')}"))
        state = RetailJourneyState.REFUND_UNKNOWN_OUTCOME if failure_after_commit else RetailJourneyState.REFUNDED
        result = RetailRefund(requested.refund_id, requested.order_id, amount, requested.currency, state, requested.idempotency_key, requested.payment_reference, receipt)
        self.refunds[refund_id] = result
        status = "UNKNOWN_OUTCOME" if failure_after_commit else "SUCCEEDED"
        if self.storage:
            if failure_after_commit:
                self.storage.record_idempotency(idempotency_key, fingerprint, status, refund_id)
                self.storage.attach_receipt(idempotency_key, fingerprint, receipt)
                self.storage.save_entity("refund", result, entity_id=refund_id, business_id=self.business_id, environment=self.environment.value)
                self.storage.add_reconciliation(reconciliation_id="reconcile-" + refund_id, logical_transaction_id="tx-" + fingerprint[:24], payload={"downstream_reference": refund_id, "reason": "refund response lost", "verification_strategy": "get_refund_status"})
            else:
                self.storage.commit_refund(refund=result, key=idempotency_key, request_hash=fingerprint, receipt=receipt, business_id=self.business_id, environment=self.environment.value)
        else:
            self.transactions.record_idempotency(idempotency_key, fingerprint, status, refund_id)
            self.transactions.attach_receipt(idempotency_key, fingerprint, receipt)
        return result

    def get_refund_status(self, refund_id: str) -> RetailJourneyState:
        return self.refunds[refund_id].state

    def _result(self, status: str, state: RetailJourneyState, message: str, quote: RetailQuote | None, trace: TraceRecorder, findings: list[str], *, order: RetailOrder | None = None, receipt: Receipt | None = None, replayed: bool = False) -> RetailResult:
        return RetailResult(status, state, message, order, quote, receipt, trace.export(), tuple(findings), replayed)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["PaymentAuthorization", "PaymentAuthorizationState", "RetailActivationBlocked", "RetailJourneyState", "RetailOrder", "RetailProduct", "RetailReferenceEnvironment", "RetailResult", "RetailReturn", "RetailRefund", "RetailVariant", "RetailQuote"]

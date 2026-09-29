from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

from agentnative.observability import TraceContext, TraceRecorder
from agentnative.ownership import Environment
from agentnative.packs.core_gates import CoreGuaranteeError, CoreGuaranteeRegistry
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

    def __init__(self, *, business_id: str, environment: Environment = Environment.SANDBOX, core_guarantees: CoreGuaranteeRegistry | None = None) -> None:
        self.business_id = business_id
        self.environment = environment
        self.core_guarantees = core_guarantees or CoreGuaranteeRegistry()
        required = ("identity_binding_v1", "delegation_scope_v1", "transaction_identity_v1", "replay_safe_confirmation_v1", "idempotency_atomicity_v1", "receipt_integrity_v1")
        try:
            self.core_guarantees.require(required)
        except CoreGuaranteeError as exc:
            raise RetailActivationBlocked(str(exc)) from exc
        self.products: dict[str, RetailProduct] = {}
        self.orders: dict[str, RetailOrder] = {}
        self.transactions = TransactionSafetyEngine()
        self.receipts = ReceiptEngine()

    def add_product(self, product: RetailProduct) -> None:
        if not product.product_id or not product.variants:
            raise ValueError("retail products require a stable ID and at least one variant")
        self.products[product.product_id] = product

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
        terms = {"shipping": shipping, "shipping_cost": 0.0 if shipping == "standard" else 12.0, "tax_status": "simulated", "inventory_observed_at": _now(), "quantity": quantity}
        quote = Quote.create(capability_id="sector.retail:submit_order", resource_reference=f"{product_id}:{variant_id}", value=total, currency=variant.currency, terms=terms, version=variant.version, principal_reference=principal_id, business_id=self.business_id, environment=self.environment, ttl=ttl, now=now, evidence_refs=(f"product:{product_id}", f"variant:{variant_id}"))
        return RetailQuote(quote, RetailJourneyState.QUOTED, product_id, variant_id, terms)

    def submit_order(self, *, retail_quote: RetailQuote, principal_id: str, agent_id: str, provider_id: str, trust_class: str, idempotency_key: str, confirmation: Confirmation | None = None, require_confirmation: bool = True, shipping_destination_ref: str = "destination:synthetic", failure_after_commit: bool = False, now: datetime | None = None) -> RetailResult:
        clock = now or datetime.now(timezone.utc)
        quote = retail_quote.quote
        trace = TraceRecorder(TraceContext.new(f"retail:{idempotency_key}"))
        findings: list[str] = []
        if trust_class not in {"VERIFIED", "PARTNER", "INTERNAL"}:
            trace.emit("retail_order_denied", {"reason": "unknown_agent"})
            return self._result("DENIED", RetailJourneyState.ORDER_REJECTED, "unknown agent cannot purchase", retail_quote, trace, findings + ["UNKNOWN_AGENT_PURCHASE"])
        if require_confirmation and confirmation is None:
            trace.emit("confirmation_requested", {"quote_id": quote.quote_id})
            return self._result("CONFIRMATION_REQUIRED", RetailJourneyState.CONFIRMATION_REQUIRED, "confirmation is required before checkout", retail_quote, trace, findings + ["CONFIRMATION_REQUIRED"])
        capability_id = "sector.retail:submit_order"
        payload = {"product_id": retail_quote.product_id, "variant_id": retail_quote.variant_id, "quantity": quote.terms.get("quantity", 1), "shipping": quote.terms.get("shipping"), "shipping_destination_ref": shipping_destination_ref}
        request_hash = self.transactions.request_hash(capability_id=capability_id, resource_reference=quote.resource_reference, value=quote.value, currency=quote.currency, input_data=payload, business_id=self.business_id, environment=self.environment, principal_id=principal_id, agent_id=agent_id, provider_id=provider_id, quote_id=quote.quote_id, confirmation_id=confirmation.confirmation_id if confirmation else None)
        try:
            existing = self.transactions.claim_idempotency(idempotency_key, request_hash, scenario_id="retail.submit_order")
            if existing is not None:
                order = self.orders.get(existing.result_reference or "")
                receipt = self.transactions.get_receipt(idempotency_key, request_hash)
                trace.emit("result_replayed", {"receipt_reference": getattr(receipt, "receipt_id", None)})
                return self._result("REPLAYED", order.state if order else RetailJourneyState.ORDER_ACCEPTED, "order result replayed", retail_quote, trace, findings, order=order, receipt=receipt, replayed=True)
            product = self.products[retail_quote.product_id]
            variant = product.variants[retail_quote.variant_id]
            TransactionSafetyEngine.check_quote(quote, capability_id=capability_id, resource_reference=quote.resource_reference, value=quote.value, currency=quote.currency, principal_reference=principal_id, business_id=self.business_id, environment=self.environment, resource_version=variant.version, now=clock)
            quantity = int(quote.terms.get("quantity", 1))
            if variant.inventory < quantity:
                raise TransactionSafetyError("INVENTORY_UNAVAILABLE", "inventory was lost before checkout")
            logical_id = self.transactions.logical_transaction_id(idempotency_key, request_hash)
            if confirmation is not None:
                self.transactions.consume_confirmation(confirmation, quote, principal_reference=principal_id, logical_transaction_id=logical_id, transaction_fingerprint=request_hash, agent_id=agent_id, provider_id=provider_id, business_id=self.business_id, environment=self.environment, now=clock)
                trace.emit("confirmation_received", {"confirmation_id": confirmation.confirmation_id})
            trace.emit("checkout_submitted", {"logical_transaction_id": logical_id, "quote_id": quote.quote_id})
            variant.inventory -= quantity
            variant.version = str(int(variant.version) + 1)
            order_id = "order-" + stable_hash({"transaction": request_hash, "logical": logical_id})[:24]
            order = RetailOrder(order_id, retail_quote.product_id, retail_quote.variant_id, principal_id, float(quote.value or 0), str(quote.currency), RetailJourneyState.ORDER_ACCEPTED, quantity, trace.context.trace_id)
            self.orders[order_id] = order
            self.transactions.record_idempotency(idempotency_key, request_hash, "SUCCEEDED", order_id, logical_id=logical_id)
            receipt = self.receipts.create(business_id=self.business_id, environment=self.environment.value, agent_id=agent_id, provider_id=provider_id, principal_reference=principal_id, capability_id=capability_id, policy_id="retail-reference-policy", policy_version="retail-0.1", decision="ALLOW", delegation_reference="retail-reference-delegation", confirmation_reference=confirmation.confirmation_id if confirmation else None, quote_reference=quote.quote_id, request_hash=request_hash, result="ORDER_ACCEPTED", side_effect="IRREVERSIBLE", resource_reference=quote.resource_reference, value=quote.value, currency=quote.currency, correlation_id=trace.context.correlation_id, trace_id=trace.context.trace_id, evidence_refs=(f"order:{order_id}", f"quote:{quote.quote_id}"))
            self.transactions.attach_receipt(idempotency_key, request_hash, receipt)
            trace.emit("order_accepted", {"order_id": order_id})
            if failure_after_commit:
                order.state = RetailJourneyState.UNKNOWN_OUTCOME
                trace.emit("unknown_outcome", {"order_id": order_id})
                return self._result("UNKNOWN_OUTCOME", RetailJourneyState.UNKNOWN_OUTCOME, "downstream order succeeded but response was lost", retail_quote, trace, findings + ["UNKNOWN_OUTCOME"], order=order, receipt=receipt)
            return self._result("ORDER_ACCEPTED", RetailJourneyState.ORDER_ACCEPTED, "order accepted", retail_quote, trace, findings, order=order, receipt=receipt)
        except TransactionSafetyError as exc:
            findings.append(exc.code)
            trace.emit("retail_order_failed", {"code": exc.code})
            return self._result("FAILED", RetailJourneyState.RECONCILIATION_REQUIRED if exc.state_changed else RetailJourneyState.ORDER_REJECTED, str(exc), retail_quote, trace, findings)

    def cancel_order(self, *, order_id: str, principal_id: str, agent_id: str, provider_id: str, idempotency_key: str) -> RetailResult:
        order = self.orders[order_id]
        if order.principal_id != principal_id:
            return RetailResult("DENIED", RetailJourneyState.ORDER_REJECTED, "principal does not own order", order=order, findings=("PRINCIPAL_MISMATCH",))
        capability_id = "sector.retail:cancel_order"
        request_hash = self.transactions.request_hash(capability_id=capability_id, resource_reference=order_id, value=0, currency="USD", input_data={"order_id": order_id, "operation": "cancel"}, business_id=self.business_id, environment=self.environment, principal_id=principal_id, agent_id=agent_id, provider_id=provider_id)
        existing = self.transactions.claim_idempotency(idempotency_key, request_hash, scenario_id="retail.cancel_order")
        if existing is not None:
            receipt = self.transactions.get_receipt(idempotency_key, request_hash)
            return RetailResult("REPLAYED", order.state, "cancellation result replayed", order=order, receipt=receipt, replayed=True)
        if order.state not in {RetailJourneyState.ORDER_ACCEPTED, RetailJourneyState.PARTIALLY_FULFILLED}:
            self.transactions.record_idempotency(idempotency_key, request_hash, "FAILED_TERMINAL", None, error_reference="CANCELLATION_NOT_ALLOWED")
            return RetailResult("DENIED", order.state, "order is not cancellable", order=order, findings=("CANCELLATION_NOT_ALLOWED",))
        trace = TraceRecorder(TraceContext.new(f"retail:cancel:{idempotency_key}"))
        trace.emit("cancellation_requested", {"order_id": order_id})
        order.state = RetailJourneyState.CANCELLED
        self.transactions.record_idempotency(idempotency_key, request_hash, "SUCCEEDED", order_id)
        receipt = self.receipts.create(business_id=self.business_id, environment=self.environment.value, agent_id=agent_id, provider_id=provider_id, principal_reference=principal_id, capability_id=capability_id, policy_id="retail-reference-policy", policy_version="retail-0.1", decision="ALLOW", delegation_reference="retail-reference-delegation", confirmation_reference=None, quote_reference=None, request_hash=request_hash, result="CANCELLED", side_effect="REVERSIBLE", resource_reference=order_id, value=0, currency="USD", correlation_id=trace.context.correlation_id, trace_id=trace.context.trace_id, evidence_refs=(f"order:{order_id}",))
        self.transactions.attach_receipt(idempotency_key, request_hash, receipt)
        trace.emit("cancellation_completed", {"order_id": order_id})
        return RetailResult("CANCELLED", RetailJourneyState.CANCELLED, "order cancelled", order=order, receipt=receipt, trace=trace.export())

    def return_eligibility(self, order_id: str) -> RetailJourneyState:
        order = self.orders[order_id]
        if order.state == RetailJourneyState.FULFILLED:
            order.state = RetailJourneyState.RETURN_ELIGIBLE
        return order.state if order.state in {RetailJourneyState.RETURN_ELIGIBLE, RetailJourneyState.RETURN_INELIGIBLE} else RetailJourneyState.RETURN_INELIGIBLE

    def set_inventory(self, product_id: str, variant_id: str, inventory: int) -> None:
        variant = self.products[product_id].variants[variant_id]
        variant.inventory = inventory
        variant.version = str(int(variant.version) + 1)

    def set_price(self, product_id: str, variant_id: str, price: float) -> None:
        variant = self.products[product_id].variants[variant_id]
        variant.price = price
        variant.version = str(int(variant.version) + 1)

    def _result(self, status: str, state: RetailJourneyState, message: str, quote: RetailQuote | None, trace: TraceRecorder, findings: list[str], *, order: RetailOrder | None = None, receipt: Receipt | None = None, replayed: bool = False) -> RetailResult:
        return RetailResult(status, state, message, order, quote, receipt, trace.export(), tuple(findings), replayed)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["RetailActivationBlocked", "RetailJourneyState", "RetailOrder", "RetailProduct", "RetailReferenceEnvironment", "RetailResult", "RetailVariant", "RetailQuote"]

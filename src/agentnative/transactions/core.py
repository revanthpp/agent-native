from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from threading import Condition, RLock
from typing import Any, Protocol
from uuid import uuid4

from agentnative.ownership.models import Environment
from agentnative.protocols.models import ActionClass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    def default(item: Any) -> str:
        if isinstance(item, datetime):
            return _iso(item)
        if isinstance(item, Decimal):
            return format(item, "f")
        if isinstance(item, StrEnum):
            return item.value
        return f"<{type(item).__name__}>"

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=default)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _identity_text(value: Any) -> str | None:
    """Normalize an identifier without changing its case-sensitive meaning."""
    if value is None:
        return None
    return str(value).strip()


def _identity_amount(value: Any) -> Any:
    """Represent numeric amounts by exact decimal text, preserving invalid types."""
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, (Decimal, int, float)):
        try:
            amount = value if isinstance(value, Decimal) else Decimal(str(value))
            if amount.is_finite():
                return {"type": "decimal", "value": format(amount.normalize(), "f")}
        except (InvalidOperation, ValueError, TypeError):
            pass
    return value


def _identity_payload(value: Any) -> Any:
    """Canonicalize action payload values while retaining their semantic types."""
    if isinstance(value, dict):
        return {str(key): _identity_payload(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_identity_payload(item) for item in value]
    if isinstance(value, set | frozenset):
        values = [_identity_payload(item) for item in value]
        return sorted(values, key=canonical_json)
    if isinstance(value, (Decimal, int, float, bool)):
        return _identity_amount(value)
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        return _iso(value)
    return value


def transaction_identity(
    *,
    business_id: str,
    environment: Environment | str,
    principal_id: str,
    agent_id: str | None,
    provider_id: str | None,
    capability_id: str,
    resource_reference: str,
    value: Any,
    currency: Any,
    input_data: dict[str, Any],
    quote_id: str | None = None,
    confirmation_id: str | None = None,
) -> dict[str, Any]:
    """Return the canonical material identity of one logical transaction.

    Scenario IDs, trace IDs, timestamps, retry counters, and transport headers
    are intentionally absent. They describe an interaction, not the business
    action. The returned structure is safe to hash and contains no raw secrets
    beyond caller-supplied identifiers already required to authorize the action.
    """
    normalized_currency, _ = normalize_currency(currency)
    if normalized_currency:
        identity_currency: Any = normalized_currency
    elif currency is None:
        identity_currency = None
    elif isinstance(currency, str):
        identity_currency = currency.strip().upper()
    else:
        identity_currency = {"type": type(currency).__name__, "value": str(currency)}
    environment_value = environment.value if isinstance(environment, StrEnum) else _identity_text(environment)
    return {
        "business_id": _identity_text(business_id),
        "environment": environment_value,
        "principal_id": _identity_text(principal_id),
        "agent_id": _identity_text(agent_id),
        "provider_id": _identity_text(provider_id),
        "capability_id": _identity_text(capability_id),
        "resource_reference": _identity_text(resource_reference),
        "value": _identity_amount(value),
        "currency": identity_currency,
        "action_payload": _identity_payload(input_data),
        "quote_id": _identity_text(quote_id),
        "confirmation_id": _identity_text(confirmation_id),
    }


def transaction_fingerprint(**kwargs: Any) -> str:
    """Hash the canonical material transaction identity with SHA-256."""
    return stable_hash(transaction_identity(**kwargs))


def logical_transaction_id(idempotency_key: str, fingerprint: str) -> str:
    """Derive a stable, non-sensitive logical transaction identifier."""
    return "txn-" + stable_hash({"idempotency_key": idempotency_key, "fingerprint": fingerprint})[:24]


def public_amount(value: Any) -> Any:
    return format(value, "f") if isinstance(value, Decimal) else value


SUPPORTED_CURRENCIES = frozenset({"AUD", "CAD", "CHF", "DKK", "EUR", "GBP", "HKD", "JPY", "NOK", "NZD", "PLN", "SEK", "SGD", "USD"})
MAX_MONEY_AMOUNT = Decimal("1000000000000000.00")


def normalize_currency(currency: Any) -> tuple[str | None, str | None]:
    if currency is None:
        return None, "RISK_CURRENCY_REQUIRED"
    if not isinstance(currency, str):
        return None, "RISK_CURRENCY_INVALID"
    normalized = currency.strip().upper()
    if not normalized:
        return None, "RISK_CURRENCY_REQUIRED"
    if normalized not in SUPPORTED_CURRENCIES:
        return None, "RISK_CURRENCY_UNSUPPORTED"
    return normalized, None


@dataclass(frozen=True)
class MonetaryValue:
    """Exact, bounded monetary input used by all risk-ceiling comparisons."""

    amount: Decimal
    currency: str

    @classmethod
    def parse(cls, value: Any, currency: Any) -> tuple["MonetaryValue | None", str | None]:
        if value is None:
            return None, "RISK_VALUE_REQUIRED"
        if isinstance(value, bool) or not isinstance(value, (Decimal, int, float)):
            return None, "RISK_VALUE_INVALID"
        try:
            amount = value if isinstance(value, Decimal) else Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return None, "RISK_VALUE_INVALID"
        if not amount.is_finite():
            return None, "RISK_VALUE_NON_FINITE"
        if amount < 0:
            return None, "RISK_VALUE_NEGATIVE"
        if amount > MAX_MONEY_AMOUNT:
            return None, "RISK_VALUE_OUT_OF_RANGE"
        normalized_currency, currency_error = normalize_currency(currency)
        if currency_error:
            return None, currency_error
        return cls(amount, normalized_currency), None


class FailureClass(StrEnum):
    RETRYABLE = "RETRYABLE"
    TERMINAL = "TERMINAL"
    UNKNOWN = "UNKNOWN"


class FailurePoint(StrEnum):
    BEFORE_PREVIEW = "BEFORE_PREVIEW"
    AFTER_PREVIEW = "AFTER_PREVIEW"
    BEFORE_POLICY = "BEFORE_POLICY"
    BEFORE_COMMIT = "BEFORE_COMMIT"
    AFTER_COMMIT_BEFORE_RESPONSE = "AFTER_COMMIT_BEFORE_RESPONSE"
    DURING_RESPONSE = "DURING_RESPONSE"
    BEFORE_VERIFICATION = "BEFORE_VERIFICATION"
    DURING_COMPENSATION = "DURING_COMPENSATION"


class TransactionSafetyError(RuntimeError):
    def __init__(self, code: str, message: str, failure_class: FailureClass = FailureClass.TERMINAL, *, state_changed: bool = False, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.failure_class = failure_class
        self.state_changed = state_changed
        self.details = dict(details or {})


class IdempotencyStatus(StrEnum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_TERMINAL = "FAILED_TERMINAL"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"


@dataclass(frozen=True)
class FailureInjection:
    point: FailurePoint
    failure_type: str
    failure_class: FailureClass = FailureClass.RETRYABLE
    occurrences: int = 1

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "FailureInjection":
        return cls(FailurePoint(str(raw.get("point") or "BEFORE_COMMIT").upper()), str(raw.get("failure_type") or "timeout"), FailureClass(str(raw.get("failure_class") or "RETRYABLE").upper()), max(1, int(raw.get("occurrences", 1))))


@dataclass(frozen=True)
class EnvironmentRiskCeiling:
    environment: Environment
    allowed_actions: frozenset[ActionClass]
    blocked_actions: frozenset[ActionClass]
    max_value: Decimal | None
    currency: str | None
    active_enabled: bool

    def allows(self, action: ActionClass, value: Any, currency: Any = None, *, validate_value: bool = True, validate_currency: bool = True, enforce_ceiling: bool = True) -> tuple[bool, str]:
        if not self.active_enabled and action not in {ActionClass.READ, ActionClass.RECOMMEND, ActionClass.PREVIEW}:
            return False, "active execution is disabled for this environment"
        if action in self.blocked_actions or action not in self.allowed_actions:
            return False, f"action {action.value} exceeds the {self.environment.value} risk ceiling"
        if self.max_value is not None and action not in {ActionClass.READ, ActionClass.RECOMMEND, ActionClass.PREVIEW}:
            if validate_value:
                parsed, error = MonetaryValue.parse(value, currency if validate_currency else self.currency)
                if error:
                    return False, error
            else:
                try:
                    parsed = MonetaryValue(Decimal("0") if value is None or isinstance(value, bool) else Decimal(str(value)), self.currency or "USD")
                except (InvalidOperation, ValueError, TypeError):
                    parsed = MonetaryValue(Decimal("0"), self.currency or "USD")
            expected_currency, currency_error = normalize_currency(self.currency)
            if validate_currency and (currency_error or parsed.currency != expected_currency):
                return False, "RISK_CURRENCY_MISMATCH"
            ceiling = Decimal(str(self.max_value))
            if enforce_ceiling and parsed.amount > ceiling:
                return False, "RISK_CEILING_EXCEEDED"
        return True, "within risk ceiling"


def default_risk_ceiling(environment: Environment) -> EnvironmentRiskCeiling:
    read_only = frozenset({ActionClass.READ, ActionClass.RECOMMEND, ActionClass.PREVIEW})
    controlled = frozenset({ActionClass.READ, ActionClass.RECOMMEND, ActionClass.PREVIEW, ActionClass.RESERVE, ActionClass.CREATE, ActionClass.UPDATE})
    all_actions = frozenset(ActionClass)
    if environment == Environment.SANDBOX:
        return EnvironmentRiskCeiling(environment, all_actions, frozenset(), Decimal("100.00"), "USD", True)
    if environment == Environment.STAGING:
        return EnvironmentRiskCeiling(environment, controlled, frozenset({ActionClass.TRANSFER, ActionClass.PURCHASE, ActionClass.REFUND, ActionClass.DELETE}), Decimal("100.00"), "USD", True)
    return EnvironmentRiskCeiling(environment, read_only, frozenset(all_actions - read_only), Decimal("0.00"), "USD", False)


@dataclass(frozen=True)
class PreviewResult:
    resource_reference: str
    resource_version: str
    value: float | None
    currency: str | None
    terms: dict[str, Any] = field(default_factory=dict)
    response_reference: str = ""


@dataclass(frozen=True)
class Quote:
    quote_id: str
    capability_id: str
    resource_reference: str
    value: float | None
    currency: str | None
    terms: dict[str, Any]
    created_at: datetime
    expires_at: datetime
    version: str
    principal_reference: str
    business_id: str
    environment: Environment
    evidence_refs: tuple[str, ...] = ()

    @classmethod
    def create(
        cls,
        *,
        capability_id: str,
        resource_reference: str,
        value: float | None,
        currency: str | None,
        terms: dict[str, Any],
        version: str,
        principal_reference: str,
        business_id: str,
        environment: Environment,
        ttl: timedelta = timedelta(minutes=5),
        now: datetime | None = None,
        evidence_refs: tuple[str, ...] = (),
    ) -> "Quote":
        created = now or _now()
        binding = {
            "capability_id": capability_id,
            "resource_reference": resource_reference,
            "value": value,
            "currency": currency,
            "terms": terms,
            "version": version,
            "principal_reference": principal_reference,
            "business_id": business_id,
            "environment": environment.value,
            "created_at": _iso(created),
        }
        quote_id = "quote-" + stable_hash(binding)[:24]
        return cls(quote_id, capability_id, resource_reference, value, currency, dict(terms), created, created + ttl, version, principal_reference, business_id, environment, evidence_refs)

    def binds_to(self, *, capability_id: str, resource_reference: str, value: float | None, currency: str | None, principal_reference: str, business_id: str, environment: Environment) -> bool:
        return (self.capability_id, self.resource_reference, self.value, self.currency, self.principal_reference, self.business_id, self.environment) == (capability_id, resource_reference, value, currency, principal_reference, business_id, environment)

    def is_valid(self, now: datetime | None = None) -> bool:
        return (now or _now()) < self.expires_at


@dataclass(frozen=True)
class Confirmation:
    confirmation_id: str
    principal_reference: str
    capability_id: str
    resource_reference: str
    value: float | None
    currency: str | None
    quote_id: str
    created_at: datetime
    expires_at: datetime
    confirmation_hash: str

    @classmethod
    def create(cls, quote: Quote, *, now: datetime | None = None, ttl: timedelta = timedelta(minutes=5)) -> "Confirmation":
        created = now or _now()
        binding = {"principal_reference": quote.principal_reference, "capability_id": quote.capability_id, "resource_reference": quote.resource_reference, "value": quote.value, "currency": quote.currency, "quote_id": quote.quote_id, "created_at": _iso(created)}
        digest = stable_hash(binding)
        return cls("confirmation-" + digest[:24], quote.principal_reference, quote.capability_id, quote.resource_reference, quote.value, quote.currency, quote.quote_id, created, created + ttl, digest)

    def binds_to(self, quote: Quote, *, principal_reference: str) -> bool:
        return self.principal_reference == principal_reference and self.quote_id == quote.quote_id and self.capability_id == quote.capability_id and self.resource_reference == quote.resource_reference and self.value == quote.value and self.currency == quote.currency

    def is_valid(self, now: datetime | None = None) -> bool:
        return (now or _now()) < self.expires_at


@dataclass(frozen=True)
class ConfirmationBinding:
    confirmation_id: str
    logical_transaction_id: str
    transaction_fingerprint: str
    principal_id: str
    agent_id: str | None
    provider_id: str | None
    business_id: str
    environment: str
    capability_id: str
    resource_reference: str
    approved_value: Any
    currency: str | None
    quote_id: str
    bound_at: datetime
    expires_at: datetime
    status: str = "BOUND"


@dataclass(frozen=True)
class IdempotencyRecord:
    idempotency_key: str
    request_hash: str
    status: str
    result_reference: str | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    scenario_id: str | None = None
    owner_execution_id: str | None = None
    error_reference: str | None = None
    expires_at: datetime | None = None
    logical_transaction_id: str | None = None
    receipt_reference: str | None = None

    @property
    def transaction_fingerprint(self) -> str:
        """Explicit name for the request hash used as the transaction identity."""
        return self.request_hash


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    result_reference: str
    state_changed: bool
    side_effect: str
    resource_version: str
    response_received: bool = True
    message: str = ""


@dataclass(frozen=True)
class VerificationResult:
    success: bool
    resource_version: str
    state_digest: str
    message: str = ""


class ExecutionAdapter(Protocol):
    def build_plan(self, scenario: Any) -> PreviewResult: ...
    def prepare(self, scenario: Any) -> None: ...
    def preview(self, scenario: Any) -> PreviewResult: ...
    def execute(self, scenario: Any, quote: Quote, idempotency_key: str) -> ExecutionResult: ...
    def verify(self, scenario: Any, execution: ExecutionResult) -> VerificationResult: ...
    def compensate(self, scenario: Any, execution: ExecutionResult) -> ExecutionResult: ...
    def snapshot(self) -> tuple[str, str]: ...


class TransactionSafetyEngine:
    """Transaction rules plus process-local atomic duplicate/confirmation stores."""

    def __init__(self, *, max_retries: int = 2) -> None:
        self.max_retries = max(0, max_retries)
        self.idempotency: dict[str, IdempotencyRecord] = {}
        self.used_confirmations: set[str] = set()
        self.confirmation_bindings: dict[str, ConfirmationBinding] = {}
        self._receipts: dict[tuple[str, str], Any] = {}
        self._idempotency_condition = Condition(RLock())
        self._confirmation_condition = Condition(RLock())

    @staticmethod
    def request_hash(
        *,
        capability_id: str,
        resource_reference: str,
        value: Any,
        currency: Any,
        input_data: dict[str, Any],
        business_id: str = "",
        environment: Environment | str = "",
        principal_id: str = "",
        agent_id: str | None = None,
        provider_id: str | None = None,
        quote_id: str | None = None,
        confirmation_id: str | None = None,
    ) -> str:
        return transaction_fingerprint(
            business_id=business_id,
            environment=environment,
            principal_id=principal_id,
            agent_id=agent_id,
            provider_id=provider_id,
            capability_id=capability_id,
            resource_reference=resource_reference,
            value=value,
            currency=currency,
            input_data=input_data,
            quote_id=quote_id,
            confirmation_id=confirmation_id,
        )

    @staticmethod
    def logical_transaction_id(idempotency_key: str, request_hash: str) -> str:
        return logical_transaction_id(idempotency_key, request_hash)

    @staticmethod
    def _conflict(key: str, current_hash: str, stored_hash: str) -> TransactionSafetyError:
        return TransactionSafetyError(
            "IDEMPOTENCY_KEY_REUSE",
            "idempotency key was reused for a different request",
            FailureClass.TERMINAL,
            details={
                "idempotency_key_hash": stable_hash(key),
                "current_transaction_fingerprint": current_hash,
                "stored_transaction_fingerprint": stored_hash,
            },
        )

    def claim_idempotency(self, key: str, request_hash: str, *, scenario_id: str | None = None, wait_timeout: float = 30.0, enforce_hash: bool = True) -> IdempotencyRecord | None:
        """Atomically reserve a key before any adapter side effect.

        The first caller returns ``None`` and owns the PENDING reservation.
        Concurrent same-request callers wait for that reservation to resolve
        and receive the completed record. This store is process-local and not
        crash-durable; UNKNOWN_OUTCOME prevents an unsafe second commit.
        """
        deadline = _now().timestamp() + max(0.0, wait_timeout)
        with self._idempotency_condition:
            while True:
                existing = self.idempotency.get(key)
                if existing is None:
                    self.idempotency[key] = IdempotencyRecord(key, request_hash, IdempotencyStatus.PENDING.value, None, _now(), _now(), scenario_id, uuid4().hex, None, None, logical_transaction_id(key, request_hash))
                    return None
                if enforce_hash and existing.request_hash != request_hash:
                    raise self._conflict(key, request_hash, existing.request_hash)
                if existing.status == IdempotencyStatus.PENDING.value:
                    remaining = deadline - _now().timestamp()
                    if remaining <= 0:
                        raise TransactionSafetyError("IDEMPOTENCY_IN_PROGRESS", "idempotency owner did not complete within the wait bound", FailureClass.UNKNOWN)
                    self._idempotency_condition.wait(timeout=remaining)
                    continue
                if existing.status == IdempotencyStatus.FAILED_RETRYABLE.value:
                    self.idempotency[key] = IdempotencyRecord(key, request_hash, IdempotencyStatus.PENDING.value, None, existing.created_at, _now(), scenario_id, uuid4().hex, None, None, existing.logical_transaction_id or logical_transaction_id(key, request_hash))
                    return None
                return existing

    def inspect_idempotency_non_atomic(self, key: str, request_hash: str, *, enforce_hash: bool = True) -> IdempotencyRecord | None:
        """Intentional mutation seam: the old check-before-claim behavior."""
        existing = self.idempotency.get(key)
        if existing and enforce_hash and existing.request_hash != request_hash:
            raise self._conflict(key, request_hash, existing.request_hash)
        return existing

    def lookup_idempotency(self, key: str, request_hash: str, *, enforce_hash: bool = True) -> IdempotencyRecord | None:
        """Read an existing record without reserving a missing key."""
        with self._idempotency_condition:
            existing = self.idempotency.get(key)
            if existing and enforce_hash and existing.request_hash != request_hash:
                raise self._conflict(key, request_hash, existing.request_hash)
            return existing

    def record_idempotency(self, key: str, request_hash: str, status: str, result_reference: str | None, *, error_reference: str | None = None, logical_id: str | None = None) -> IdempotencyRecord:
        with self._idempotency_condition:
            existing = self.idempotency.get(key)
            if existing and existing.request_hash != request_hash:
                raise self._conflict(key, request_hash, existing.request_hash)
            record = IdempotencyRecord(key, request_hash, str(status), result_reference, existing.created_at if existing else _now(), _now(), existing.scenario_id if existing else None, existing.owner_execution_id if existing else None, error_reference, None, logical_id or (existing.logical_transaction_id if existing else logical_transaction_id(key, request_hash)), existing.receipt_reference if existing else None)
            self.idempotency[key] = record
            self._idempotency_condition.notify_all()
            return record

    def attach_receipt(self, key: str, request_hash: str, receipt: Any) -> None:
        """Associate the one canonical business-action receipt with a transaction."""
        with self._idempotency_condition:
            self._receipts[(key, request_hash)] = receipt
            existing = self.idempotency.get(key)
            if existing and existing.request_hash == request_hash:
                self.idempotency[key] = IdempotencyRecord(existing.idempotency_key, existing.request_hash, existing.status, existing.result_reference, existing.created_at, existing.updated_at, existing.scenario_id, existing.owner_execution_id, existing.error_reference, existing.expires_at, existing.logical_transaction_id, getattr(receipt, "receipt_id", None))
            self._idempotency_condition.notify_all()

    def get_receipt(self, key: str, request_hash: str, *, wait_timeout: float = 0.0) -> Any | None:
        deadline = _now().timestamp() + max(0.0, wait_timeout)
        with self._idempotency_condition:
            while True:
                receipt = self._receipts.get((key, request_hash))
                if receipt is not None or wait_timeout <= 0:
                    return receipt
                remaining = deadline - _now().timestamp()
                if remaining <= 0:
                    return None
                self._idempotency_condition.wait(timeout=remaining)

    def consume_confirmation(
        self,
        confirmation: Confirmation,
        quote: Quote,
        *,
        principal_reference: str,
        logical_transaction_id: str | None = None,
        transaction_fingerprint: str | None = None,
        agent_id: str | None = None,
        provider_id: str | None = None,
        business_id: str | None = None,
        environment: Environment | str | None = None,
        now: datetime | None = None,
        enforce_binding: bool = True,
        enforce_replay: bool = True,
        enforce_expiry: bool = True,
    ) -> None:
        # Calls that do not provide a logical transaction retain legacy direct
        # single-use behavior. The simulator always supplies the stable ID.
        logical_id = logical_transaction_id or "legacy-confirmation-call-" + uuid4().hex
        fingerprint = transaction_fingerprint or stable_hash({"confirmation_id": confirmation.confirmation_id, "quote_id": quote.quote_id, "principal": principal_reference})
        if enforce_expiry and (not confirmation.is_valid(now) or not quote.is_valid(now)):
            raise TransactionSafetyError("CONFIRMATION_OR_QUOTE_EXPIRED", "confirmation or quote is expired", FailureClass.TERMINAL)
        if enforce_binding and not confirmation.binds_to(quote, principal_reference=principal_reference):
            raise TransactionSafetyError("CONFIRMATION_CONTEXT_MISMATCH", "confirmation is not bound to this action", FailureClass.TERMINAL)
        with self._confirmation_condition:
            existing = self.confirmation_bindings.get(confirmation.confirmation_id)
            if existing and enforce_replay:
                if existing.logical_transaction_id != logical_id:
                    raise TransactionSafetyError("CONFIRMATION_REPLAY", "confirmation is already bound to a different transaction", FailureClass.TERMINAL)
                if existing.transaction_fingerprint != fingerprint:
                    raise TransactionSafetyError("CONFIRMATION_CONTEXT_MISMATCH", "confirmation is bound to a different transaction fingerprint", FailureClass.TERMINAL)
                return
            binding = ConfirmationBinding(
                confirmation.confirmation_id,
                logical_id,
                fingerprint,
                principal_reference,
                agent_id,
                provider_id,
                business_id or quote.business_id,
                environment.value if isinstance(environment, StrEnum) else str(environment or quote.environment.value),
                quote.capability_id,
                quote.resource_reference,
                quote.value,
                quote.currency,
                quote.quote_id,
                now or _now(),
                confirmation.expires_at,
            )
            self.confirmation_bindings[confirmation.confirmation_id] = binding
            self.used_confirmations.add(confirmation.confirmation_id)

    @staticmethod
    def check_quote(quote: Quote, *, capability_id: str, resource_reference: str, value: float | None, currency: str | None, principal_reference: str, business_id: str, environment: Environment, resource_version: str, now: datetime | None = None, enforce_expiry: bool = True, enforce_binding: bool = True, enforce_version: bool = True) -> None:
        if enforce_expiry and not quote.is_valid(now):
            raise TransactionSafetyError("QUOTE_EXPIRED", "quote is expired", FailureClass.TERMINAL)
        if enforce_binding and not quote.binds_to(capability_id=capability_id, resource_reference=resource_reference, value=value, currency=currency, principal_reference=principal_reference, business_id=business_id, environment=environment):
            raise TransactionSafetyError("QUOTE_CONTEXT_MISMATCH", "quote is not bound to this action", FailureClass.TERMINAL)
        if enforce_version and quote.version != resource_version:
            raise TransactionSafetyError("TOCTOU_RESOURCE_CHANGED", "resource changed after preview", FailureClass.TERMINAL)

    @staticmethod
    def classify_failure(exc: BaseException) -> FailureClass:
        if isinstance(exc, TransactionSafetyError):
            return exc.failure_class
        return FailureClass.UNKNOWN


__all__ = [
    "Confirmation",
    "ConfirmationBinding",
    "EnvironmentRiskCeiling",
    "ExecutionAdapter",
    "ExecutionResult",
    "FailureClass",
    "FailureInjection",
    "FailurePoint",
    "IdempotencyRecord",
    "IdempotencyStatus",
    "MAX_MONEY_AMOUNT",
    "MonetaryValue",
    "PreviewResult",
    "Quote",
    "TransactionSafetyEngine",
    "TransactionSafetyError",
    "logical_transaction_id",
    "transaction_fingerprint",
    "transaction_identity",
    "VerificationResult",
    "canonical_json",
    "default_risk_ceiling",
    "normalize_currency",
    "public_amount",
    "stable_hash",
]

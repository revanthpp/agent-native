from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentnative.security.sanitize import Sanitizer
from agentnative.transactions.core import canonical_json, public_amount, stable_hash, transaction_fingerprint


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Receipt:
    receipt_id: str
    timestamp: str
    business_id: str
    environment: str
    agent_id: str
    provider_id: str
    principal_reference: str
    capability_id: str
    policy_id: str | None
    policy_version: str
    decision: str
    delegation_reference: str | None
    confirmation_reference: str | None
    quote_reference: str | None
    request_hash: str
    result: str
    side_effect: str
    resource_reference: str
    value: Any
    currency: str | None
    correlation_id: str
    trace_id: str
    evidence_refs: tuple[str, ...]
    integrity: str

    def payload(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
            "business_id": self.business_id,
            "environment": self.environment,
            "agent_id": self.agent_id,
            "provider_id": self.provider_id,
            "principal_reference": self.principal_reference,
            "capability_id": self.capability_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "decision": self.decision,
            "delegation_reference": self.delegation_reference,
            "confirmation_reference": self.confirmation_reference,
            "quote_reference": self.quote_reference,
            "request_hash": self.request_hash,
            "result": self.result,
            "side_effect": self.side_effect,
            "resource_reference": self.resource_reference,
            "value": public_amount(self.value),
            "currency": self.currency,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "evidence_refs": list(self.evidence_refs),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "integrity": self.integrity}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Receipt":
        values = dict(raw)
        values["evidence_refs"] = tuple(values.get("evidence_refs", ()))
        return cls(**values)


@dataclass(frozen=True)
class ReceiptVerification:
    status: str
    reason: str
    receipt_id: str | None = None


class ReceiptEngine:
    def __init__(self, *, integrity_enabled: bool = True, redaction_enabled: bool = True) -> None:
        self.integrity_enabled = integrity_enabled
        self.redaction_enabled = redaction_enabled

    def _safe_reference(self, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value
        return Sanitizer().text(value)[0] if self.redaction_enabled else value

    @staticmethod
    def request_hash(*, capability_id: str, resource_reference: str, value: Any, currency: str | None, input_data: dict[str, Any], business_id: str = "", environment: str = "", principal_id: str = "", agent_id: str | None = None, provider_id: str | None = None, quote_id: str | None = None, confirmation_id: str | None = None) -> str:
        return transaction_fingerprint(business_id=business_id, environment=environment, principal_id=principal_id, agent_id=agent_id, provider_id=provider_id, capability_id=capability_id, resource_reference=resource_reference, value=value, currency=currency, input_data=input_data, quote_id=quote_id, confirmation_id=confirmation_id)

    def _integrity(self, payload: dict[str, Any]) -> str:
        return "sha256:" + stable_hash(payload) if self.integrity_enabled else "sha256:disabled"

    def create(self, *, business_id: str, environment: str, agent_id: str, provider_id: str, principal_reference: str, capability_id: str, policy_id: str | None, policy_version: str, decision: str, delegation_reference: str | None, confirmation_reference: str | None, quote_reference: str | None, request_hash: str, result: str, side_effect: str, resource_reference: str, value: Any, currency: str | None, correlation_id: str, trace_id: str, evidence_refs: tuple[str, ...] = ()) -> Receipt:
        safe_reference = self._safe_reference
        payload = {
            "receipt_id": "receipt-" + uuid4().hex[:24],
            "timestamp": _timestamp(),
            "business_id": safe_reference(business_id),
            "environment": safe_reference(environment),
            "agent_id": safe_reference(agent_id),
            "provider_id": safe_reference(provider_id),
            "principal_reference": safe_reference(principal_reference),
            "capability_id": safe_reference(capability_id),
            "policy_id": safe_reference(policy_id),
            "policy_version": policy_version,
            "decision": decision,
            "delegation_reference": safe_reference(delegation_reference),
            "confirmation_reference": safe_reference(confirmation_reference),
            "quote_reference": safe_reference(quote_reference),
            "request_hash": request_hash,
            "result": result,
            "side_effect": side_effect,
            "resource_reference": safe_reference(resource_reference),
            "value": public_amount(value),
            "currency": currency,
            "correlation_id": correlation_id,
            "trace_id": trace_id,
            "evidence_refs": tuple(safe_reference(item) or "" for item in evidence_refs),
        }
        return Receipt(**payload, integrity=self._integrity(payload))

    def verify(self, receipt: Receipt | dict[str, Any]) -> ReceiptVerification:
        if isinstance(receipt, Receipt):
            candidate = receipt.to_dict()
        elif isinstance(receipt, dict):
            candidate = dict(receipt)
        else:
            return ReceiptVerification("UNSUPPORTED", "receipt must be an object")
        integrity = candidate.pop("integrity", None)
        receipt_id = candidate.get("receipt_id") if isinstance(candidate.get("receipt_id"), str) else None
        if not isinstance(integrity, str) or not receipt_id:
            return ReceiptVerification("UNSUPPORTED", "receipt lacks required integrity fields", receipt_id)
        if integrity != self._integrity(candidate):
            return ReceiptVerification("INVALID", "receipt integrity mismatch", receipt_id)
        return ReceiptVerification("VALID", "receipt integrity verified", receipt_id)

    def verify_file(self, path: str | Path) -> ReceiptVerification:
        try:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ReceiptVerification("UNSUPPORTED", "receipt file is not valid JSON")
        return self.verify(value)

    @staticmethod
    def write(receipt: Receipt, path: str | Path) -> None:
        Path(path).write_text(json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = ["Receipt", "ReceiptEngine", "ReceiptVerification"]

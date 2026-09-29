from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CoreGuarantee:
    guarantee_id: str
    verified: bool
    evidence_ref: str | None = None
    independently_verified: bool = False
    core_version: str = ""


class CoreGuaranteeError(RuntimeError):
    pass


class CoreGuaranteeRegistry:
    """Explicit gate for pack claims that depend on v2 safety guarantees."""

    def __init__(self, guarantees: Iterable[CoreGuarantee] = ()) -> None:
        self._items = {item.guarantee_id: item for item in guarantees}

    def missing(self, required: Iterable[str]) -> tuple[str, ...]:
        return tuple(sorted(
            guarantee_id
            for guarantee_id in set(required)
            if not (self._items.get(guarantee_id) and self._items[guarantee_id].verified and self._items[guarantee_id].independently_verified)
        ))

    def require(self, required: Iterable[str]) -> None:
        missing = self.missing(required)
        if missing:
            raise CoreGuaranteeError("required core guarantees are not independently verified: " + ", ".join(missing))

    def evidence(self, guarantee_id: str) -> CoreGuarantee | None:
        return self._items.get(guarantee_id)

    @classmethod
    def for_test(cls, *, core_version: str = "test") -> "CoreGuaranteeRegistry":
        required = (
            "identity_binding_v1",
            "delegation_scope_v1",
            "transaction_identity_v1",
            "replay_safe_confirmation_v1",
            "idempotency_atomicity_v1",
            "receipt_integrity_v1",
        )
        return cls(CoreGuarantee(item, True, f"test:{item}", True, core_version) for item in required)


__all__ = ["CoreGuarantee", "CoreGuaranteeError", "CoreGuaranteeRegistry"]

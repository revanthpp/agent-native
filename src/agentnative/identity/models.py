from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class TrustClass(StrEnum):
    UNKNOWN = "UNKNOWN"; DECLARED = "DECLARED"; CRYPTOGRAPHICALLY_VERIFIED = "CRYPTOGRAPHICALLY_VERIFIED"; PARTNER = "PARTNER"; INTERNAL = "INTERNAL"


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str; provider_id: str; display_name: str; trust_class: TrustClass = TrustClass.UNKNOWN; identity_method: str = "unknown"; key_id: str | None = None; verified_at: datetime | None = None; expires_at: datetime | None = None; supported_protocols: tuple[str, ...] = (); declared_purpose: str = ""
    @classmethod
    def from_integrity(cls, *, provider_id, display_name, integrity, supported_protocols=(), declared_purpose=""):
        if not getattr(integrity, "valid", False) or not getattr(integrity, "agent_id", None) or not getattr(integrity, "key_id", None): raise ValueError("cryptographic verification is required")
        return cls(integrity.agent_id, provider_id, display_name, TrustClass.CRYPTOGRAPHICALLY_VERIFIED, "HTTP_MESSAGE_SIGNATURE", integrity.key_id, datetime.now(timezone.utc), None, supported_protocols, declared_purpose)

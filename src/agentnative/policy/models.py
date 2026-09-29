from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Decision(StrEnum):
    ALLOW = "ALLOW"; DENY = "DENY"; REQUIRE_HUMAN = "REQUIRE_HUMAN"; ALLOW_WITH_LIMITS = "ALLOW_WITH_LIMITS"


@dataclass(frozen=True)
class PolicyRule:
    policy_id: str; trust_class: str | None = None; provider_id: str | None = None; agent_id: str | None = None; principal_type: str | None = None; capability: str | None = None; resource: str | None = None; environment: str | None = None; geography: str | None = None; data_class: str | None = None; value_limit: float | None = None; required_confirmation: bool = False; decision: Decision = Decision.DENY; reason: str = ""; version: str = "1"; effective_at: datetime | None = None; expires_at: datetime | None = None; owner: str | None = None; priority: int = 0


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision; matched_policy: str | None; policy_version: str; reason: str; missing_conditions: tuple[str, ...] = (); required_next_action: str | None = None

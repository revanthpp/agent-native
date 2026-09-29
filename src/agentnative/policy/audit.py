from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from agentnative.policy.engine import PolicyEngine
from agentnative.policy.models import PolicyRule


@dataclass(frozen=True)
class PolicyAudit:
    policy_id: str; old_version: str | None; new_version: str; changed_by: str; changed_at: str; change_summary: str; change_hash: str


class VersionedPolicyStore:
    def __init__(self): self._versions, self._current, self._audit = {}, {}, []
    def activate(self, policy_id: str, version: str, rules: list[PolicyRule], changed_by: str, summary: str) -> PolicyAudit:
        if (policy_id, version) in self._versions: raise ValueError("policy versions are immutable")
        old=self._current.get(policy_id); self._versions[(policy_id, version)]=PolicyEngine(rules, version); self._current[policy_id]=version; payload=json.dumps({"policy_id":policy_id,"old":old,"new":version,"summary":summary},sort_keys=True).encode(); audit=PolicyAudit(policy_id,old,version,changed_by,datetime.now(timezone.utc).isoformat(),summary,hashlib.sha256(payload).hexdigest()); self._audit.append(audit); return audit
    def get(self, policy_id: str, version: str | None = None) -> PolicyEngine:
        selected=version or self._current.get(policy_id)
        if selected is None or (policy_id, selected) not in self._versions: raise KeyError("unknown policy version")
        return self._versions[(policy_id, selected)]
    def audit(self) -> tuple[PolicyAudit, ...]: return tuple(self._audit)

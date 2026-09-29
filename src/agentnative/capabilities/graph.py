from __future__ import annotations

import copy
import re

from agentnative.capabilities.models import Capability, SideEffect


class CapabilityGraph:
    """Canonical, provenance-preserving and monotonic capability graph."""

    def __init__(self, business_id: str) -> None:
        self.business_id = business_id
        self._items: dict[str, Capability] = {}

    @staticmethod
    def semantic_key(capability: Capability) -> str:
        return re.sub(r"[^a-z0-9]+", " ", capability.name.lower()).strip() or capability.capability_id.lower()

    def add(self, capability: Capability) -> Capability:
        key = self.semantic_key(capability)
        current = self._items.get(key)
        if current is None:
            current = copy.deepcopy(capability)
            current.capability_id, current.business_id = f"cap:{key}", self.business_id
            self._items[key] = current
            return current
        for source in capability.protocol_sources:
            if source not in current.protocol_sources: current.protocol_sources.append(source)
        current.evidence_refs.extend(capability.evidence_refs)
        rank = {SideEffect.NONE: 0, SideEffect.UNKNOWN: 1, SideEffect.REVERSIBLE: 2, SideEffect.IRREVERSIBLE: 3}
        if rank[capability.side_effect] > rank[current.side_effect]: current.side_effect = capability.side_effect
        return current

    def extend(self, capabilities: list[Capability]) -> None:
        for capability in capabilities: self.add(capability)

    def values(self) -> list[Capability]: return list(self._items.values())

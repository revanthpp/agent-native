from __future__ import annotations

from typing import Any

from agentnative.protocols.base import ProtocolAdapter
from agentnative.capabilities.models import Capability
from agentnative.protocols.models import ActionClass, AdapterResult, EvidenceRef, Limitation, ProtocolArtifact, SideEffect


class A2AAdapter(ProtocolAdapter):
    protocol_family = "A2A"; protocol_version = "1.0.0"

    def detect(self, document: Any) -> bool: return isinstance(document, dict) and "skills" in document

    def parse(self, document: Any, uri: str = "memory://agent-card") -> AdapterResult:
        result = AdapterResult("A2A", self.protocol_version, self.adapter_version, "agent-card", [ProtocolArtifact(uri, "a2a-agent-card")]); result.detected = self.detect(document)
        if not isinstance(document, dict) or not result.detected:
            result.validity = "NOT_DETECTED"
            return result
        if not isinstance(document.get("name"), str) or not isinstance(document.get("skills"), list):
            result.validity = "INVALID"
            result.add_error("A2A_AGENT_CARD_INVALID", "Agent Card requires name and skills list", artifact=result.artifacts[0])
            return result
        seen: set[str] = set()
        for index, skill in enumerate(document["skills"]):
            if not isinstance(skill, dict) or not isinstance(skill.get("id") or skill.get("name"), str): result.limitations.append(Limitation("A2A_INVALID_SKILL", "skill must have an id or name", f"/skills/{index}")); continue
            name = str(skill.get("id") or skill.get("name"))
            if name in seen: result.limitations.append(Limitation("A2A_DUPLICATE_SKILL", "skill identifier is duplicated", f"/skills/{index}"))
            seen.add(name); result.capabilities.append(Capability(f"a2a:{name}", "unknown", name, str(skill.get("description") or ""), [uri], ActionClass.RECOMMEND, side_effect=SideEffect.UNKNOWN, evidence_refs=[EvidenceRef(uri, f"/skills/{index}", "a2a-skill", .9)]))
        auth = document.get("authentication") or document.get("auth")
        if auth is not None and not isinstance(auth, dict): result.limitations.append(Limitation("A2A_INVALID_AUTH", "authentication declaration must be an object", "/authentication"))
        elif isinstance(auth, dict): result.auth_requirements.append(auth)
        if document.get("streaming") or document.get("streamingCapabilities"): result.limitations.append(Limitation("A2A_STREAMING_UNTESTED", "streaming is declared but not actively tested in Phase 2A", "/streaming"))
        result.limitations.append(Limitation("A2A_TRUST_SEPARATE", "Agent Card compatibility does not establish agent trust", uri)); result.validity = "VALID_WITH_WARNINGS" if result.limitations else "VALID"; return result

    def validate(self, document: Any) -> list[str]: return self.parse(document).errors
    def normalize(self, document: Any, uri: str = "memory://agent-card") -> AdapterResult: return self.parse(document, uri)
    def enumerate_auth_requirements(self, document: Any, uri: str = "memory://agent-card") -> list[dict[str, Any]]: return self.parse(document, uri).auth_requirements
    def enumerate_actions(self, document: Any, uri: str = "memory://agent-card") -> list[Any]: return self.parse(document, uri).capabilities

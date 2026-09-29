from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from agentnative.protocols.models import AdapterResult


class ProtocolAdapter(ABC):
    protocol_family = "UNKNOWN"
    protocol_version = "unknown"
    adapter_version = "2.0.0a1"

    @abstractmethod
    def detect(self, document: Any) -> bool: ...

    @abstractmethod
    def parse(self, document: Any, uri: str = "memory://artifact") -> AdapterResult: ...

    def validate(self, document: Any) -> list[str]: return self.parse(document).errors
    def normalize(self, document: Any, uri: str = "memory://artifact") -> AdapterResult: return self.parse(document, uri)
    def enumerate_capabilities(self, document: Any, uri: str = "memory://artifact") -> list[Any]: return self.normalize(document, uri).capabilities
    def enumerate_auth_requirements(self, document: Any, uri: str = "memory://artifact") -> list[dict[str, Any]]: return self.normalize(document, uri).auth_requirements
    def enumerate_actions(self, document: Any, uri: str = "memory://artifact") -> list[Any]: return self.enumerate_capabilities(document, uri)
    def enumerate_errors(self, document: Any, uri: str = "memory://artifact") -> list[str]: return self.normalize(document, uri).errors
    def enumerate_protocol_limitations(self, document: Any, uri: str = "memory://artifact") -> list[Any]: return self.normalize(document, uri).limitations

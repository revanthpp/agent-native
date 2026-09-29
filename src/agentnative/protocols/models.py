"""Shared protocol value objects owned by the canonical v2 package."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import hashlib
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agentnative.capabilities.models import Capability


class ActionClass(StrEnum):
    READ = "READ"
    RECOMMEND = "RECOMMEND"
    PREVIEW = "PREVIEW"
    RESERVE = "RESERVE"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    TRANSFER = "TRANSFER"
    PURCHASE = "PURCHASE"
    REFUND = "REFUND"
    UNKNOWN = "UNKNOWN"


class SideEffect(StrEnum):
    NONE = "NONE"
    REVERSIBLE = "REVERSIBLE"
    IRREVERSIBLE = "IRREVERSIBLE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EvidenceRef:
    source: str
    pointer: str
    method: str = "direct"
    confidence: float = 1.0


@dataclass(frozen=True)
class Limitation:
    code: str
    reason: str
    resource: str | None = None


@dataclass(frozen=True)
class ProtocolArtifact:
    uri: str
    kind: str
    content_hash: str | None = None

    @property
    def source_uri(self) -> str:
        return self.uri

    @property
    def artifact_id(self) -> str:
        return "artifact-" + hashlib.sha256(f"{self.uri}:{self.content_hash or ''}".encode()).hexdigest()[:24]

    @property
    def acquisition_evidence(self) -> str:
        return "safe-acquisition-policy" if self.kind == "openapi-ref" else "parser-input"


@dataclass(frozen=True)
class AdapterError:
    """Public, sanitized error evidence returned by a protocol adapter."""

    status: str
    error_code: str
    message: str
    protocol: str
    artifact_reference: str | None = None
    sanitized_details: dict[str, Any] = field(default_factory=dict)
    category: str = "TARGET_INPUT_INVALID"
    operation: str = "parse"

    @property
    def code(self) -> str:
        """Compatibility alias for callers that use limitation-style codes."""

        return self.error_code


@dataclass
class AdapterResult:
    protocol_family: str
    protocol_version: str
    adapter_version: str
    conformance_profile: str
    artifacts: list[ProtocolArtifact] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    auth_requirements: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[Limitation] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    error_details: list[AdapterError] = field(default_factory=list)
    detected: bool = False
    validity: str = "NOT_DETECTED"

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def status(self) -> str:
        """Canonical status spelling for structured adapter consumers."""

        return self.validity

    def add_error(
        self,
        error_code: str,
        message: str,
        *,
        category: str = "TARGET_INPUT_INVALID",
        operation: str = "parse",
        artifact: ProtocolArtifact | None = None,
        sanitized_details: dict[str, Any] | None = None,
    ) -> None:
        """Add a stable public error while retaining legacy string errors.

        Callers provide only safe, deliberately selected details. The final
        mapping is passed through the public sanitizer as a defense in depth
        measure before it becomes part of the result object.
        """

        from agentnative.security.sanitize import Sanitizer

        safe_details = Sanitizer().value(sanitized_details or {})
        if not isinstance(safe_details, dict):
            safe_details = {}
        if artifact is not None:
            safe_details.setdefault("source_uri", Sanitizer().uri(artifact.source_uri))
            safe_details.setdefault("content_hash", artifact.content_hash)
            safe_details.setdefault("acquisition_evidence", artifact.acquisition_evidence)
        self.errors.append(message)
        self.error_details.append(
            AdapterError(
                status=self.validity,
                error_code=error_code,
                message=message,
                protocol=self.protocol_family,
                artifact_reference=artifact.artifact_id if artifact else None,
                sanitized_details=safe_details,
                category=category,
                operation=operation,
            )
        )


__all__ = [
    "ActionClass",
    "AdapterError",
    "AdapterResult",
    "EvidenceRef",
    "Limitation",
    "ProtocolArtifact",
    "SideEffect",
]

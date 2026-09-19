from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from agentnative.security.sanitize import Sanitizer


class ResultStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    NOT_OBSERVED = "NOT_OBSERVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class Severity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SideEffect(StrEnum):
    NONE = "NONE"
    REVERSIBLE = "REVERSIBLE"
    IRREVERSIBLE = "IRREVERSIBLE"
    UNKNOWN = "UNKNOWN"


class ArtifactStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    ACQUIRED = "ACQUIRED"
    PARSED = "PARSED"
    PARSE_ERROR = "PARSE_ERROR"
    ACQUISITION_ERROR = "ACQUISITION_ERROR"


class ExecutionStatus(StrEnum):
    COMPLETED = "completed"
    POLICY_BLOCKED = "policy_blocked"
    ACQUISITION_ERROR = "acquisition_error"
    INTERNAL_ERROR = "internal_error"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Target:
    raw: str
    canonical: str
    kind: str


@dataclass
class Artifact:
    uri: str
    artifact_type: str
    content: str
    content_hash: str
    acquisition_timestamp: str
    media_type: str | None = None
    status_code: int | None = None
    headers: dict[str, str] = field(default_factory=dict)
    error: str | None = None
    artifact_id: str = ""
    parse_status: ArtifactStatus = ArtifactStatus.ACQUIRED

    def __post_init__(self) -> None:
        if not self.artifact_id:
            self.artifact_id = f"artifact-{uuid5(NAMESPACE_URL, self.uri)}"

    @property
    def byte_size(self) -> int:
        return len(self.content.encode("utf-8"))


@dataclass(frozen=True)
class ArtifactSummary:
    artifact_id: str
    source_uri: str
    artifact_type: str
    content_type: str | None
    byte_size: int
    content_hash: str
    acquisition_timestamp: str
    status_code: int | None
    parse_status: str
    redaction_status: str
    error: str | None = None

    @classmethod
    def from_artifact(cls, artifact: Artifact) -> "ArtifactSummary":
        sanitizer = Sanitizer()
        return cls(
            artifact_id=artifact.artifact_id,
            source_uri=sanitizer.uri(artifact.uri),
            artifact_type=artifact.artifact_type,
            content_type=artifact.media_type,
            byte_size=artifact.byte_size,
            content_hash=artifact.content_hash,
            acquisition_timestamp=artifact.acquisition_timestamp,
            status_code=artifact.status_code,
            parse_status=artifact.parse_status.value,
            redaction_status="redacted" if sanitizer.detector.detect_text(artifact.content) else "not_required",
            error=sanitizer.text(artifact.error)[0] if artifact.error else None,
        )


@dataclass
class Operation:
    operation_id: str
    method: str
    path: str
    summary: str = ""
    description: str = ""
    parameters: list[dict[str, Any]] = field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: dict[str, Any] = field(default_factory=dict)
    security: list[dict[str, list[str]]] = field(default_factory=list)
    extensions: dict[str, Any] = field(default_factory=dict)
    source_uri: str = ""

    @property
    def text(self) -> str:
        return " ".join((self.operation_id, self.summary, self.description, self.path)).lower()

    @property
    def side_effect(self) -> SideEffect:
        return self.risk.classification

    @property
    def risk(self) -> "OperationRisk":
        return classify_operation(self)


@dataclass(frozen=True)
class OperationRisk:
    classification: SideEffect
    structural: SideEffect
    declared: SideEffect | None
    contradiction: bool
    reason: str


def classify_operation(operation: Operation) -> OperationRisk:
    method = operation.method.upper()
    if method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
        structural = SideEffect.NONE
    elif method == "DELETE" or any(word in operation.text for word in ("destroy", "purchase", "transfer")):
        structural = SideEffect.IRREVERSIBLE
    elif method in {"PUT", "PATCH"}:
        structural = SideEffect.REVERSIBLE
    else:
        structural = SideEffect.UNKNOWN

    declared: SideEffect | None = None
    raw_declared = operation.extensions.get("x-side-effect") or operation.extensions.get("x-side_effect")
    if isinstance(raw_declared, str):
        try:
            declared = SideEffect(raw_declared.upper())
        except ValueError:
            declared = None

    contradiction = False
    if declared is not None:
        if structural == SideEffect.NONE and declared != SideEffect.NONE:
            contradiction = True
        elif structural in {SideEffect.REVERSIBLE, SideEffect.IRREVERSIBLE} and declared == SideEffect.NONE:
            contradiction = True
        elif structural == SideEffect.IRREVERSIBLE and declared != SideEffect.IRREVERSIBLE:
            contradiction = True

    if "read-only" in operation.text or "read only" in operation.text:
        if structural != SideEffect.NONE:
            contradiction = True

    if structural == SideEffect.NONE:
        classification = SideEffect.NONE if declared in {None, SideEffect.NONE} else SideEffect.UNKNOWN
    elif structural == SideEffect.IRREVERSIBLE:
        classification = SideEffect.IRREVERSIBLE
    elif structural == SideEffect.REVERSIBLE:
        classification = SideEffect.IRREVERSIBLE if declared == SideEffect.IRREVERSIBLE else SideEffect.REVERSIBLE
    else:
        classification = declared if declared not in {None, SideEffect.NONE} else SideEffect.UNKNOWN

    reason = f"{method} structurally classified as {structural.value}"
    if declared is not None:
        reason += f"; declaration={declared.value}"
    if contradiction:
        reason += "; contradiction preserved"
    return OperationRisk(classification, structural, declared, contradiction, reason)


@dataclass
class OpenAPIDocument:
    uri: str
    version: str | None
    title: str | None
    security_schemes: dict[str, dict[str, Any]]
    operations: list[Operation]
    raw: dict[str, Any]


@dataclass(frozen=True)
class Limitation:
    code: str
    resource: str | None
    reason: str

    def __str__(self) -> str:
        location = f" at {self.resource}" if self.resource else ""
        return f"{self.code}{location}: {self.reason}"


@dataclass
class DiscoveredSurface:
    identity: dict[str, Any] = field(default_factory=dict)
    structured_metadata: list[dict[str, Any]] = field(default_factory=list)
    openapi: list[OpenAPIDocument] = field(default_factory=list)
    agent_metadata: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    limitations: list[Limitation] = field(default_factory=list)

    @property
    def operations(self) -> list[Operation]:
        return [operation for document in self.openapi for operation in document.operations]

    @property
    def security_schemes(self) -> dict[str, dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for document in self.openapi:
            merged.update(document.security_schemes)
        return merged


@dataclass
class Evidence:
    evidence_id: str
    source_uri: str
    artifact_type: str
    acquisition_timestamp: str
    content_hash: str
    artifact_id: str
    check_id: str
    relevant_fragment: str
    normalized_representation: dict[str, Any]
    observation: str
    confidence: float
    redaction_status: str = "not_required"


@dataclass(frozen=True)
class CheckDefinition:
    id: str
    name: str
    domain: str
    version: str
    severity: Severity
    description: str
    rationale: str
    evidence_required: str
    evaluation_method: str
    remediation: str
    references: tuple[str, ...]
    passive_or_active: str
    confidence_method: str


@dataclass
class CheckResult:
    check: CheckDefinition
    status: ResultStatus
    explanation: str
    remediation: str
    confidence: float
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class ScanReport:
    scan_id: str
    target: Target
    started_at: str
    completed_at: str
    version: str
    check_set_version: str
    results: list[CheckResult]
    artifacts: list[Artifact]
    limitations: list[Limitation] = field(default_factory=list)
    execution_status: ExecutionStatus = ExecutionStatus.COMPLETED

    def summary(self) -> dict[str, int]:
        counts = {status.value: 0 for status in ResultStatus}
        for result in self.results:
            counts[result.status.value] += 1
        return counts

    def domain_summary(self) -> dict[str, dict[str, int]]:
        domains: dict[str, dict[str, int]] = {}
        for result in self.results:
            counts = domains.setdefault(result.check.domain, {status.value: 0 for status in ResultStatus})
            counts[result.status.value] += 1
        return domains

    def to_dict(self) -> dict[str, Any]:
        return self.public_projection().to_dict()

    def public_projection(self) -> "PublicReport":
        from agentnative.reporting.safe import SafeReportBuilder

        return SafeReportBuilder().build(self)


@dataclass
class PublicReport:
    """Sanitized report projection. Raw Artifact.content never crosses this boundary."""

    scan_id: str
    target: Target
    started_at: str
    completed_at: str
    version: str
    check_set_version: str
    execution_status: ExecutionStatus
    results: list[CheckResult]
    artifacts: list[ArtifactSummary]
    limitations: list[Limitation]
    summary: dict[str, int]
    domains: dict[str, dict[str, int]]

    def to_dict(self) -> dict[str, Any]:
        def clean(value: Any, field_name: str | None = None) -> Any:
            if isinstance(value, StrEnum):
                return value.value
            if hasattr(value, "__dataclass_fields__"):
                return {key: clean(getattr(value, key), key) for key in value.__dataclass_fields__}
            if isinstance(value, list):
                return [clean(item, field_name) for item in value]
            if isinstance(value, dict):
                return {key: clean(item, key) for key, item in value.items()}
            return value

        return clean(self)

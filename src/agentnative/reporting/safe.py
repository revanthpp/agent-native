from __future__ import annotations

from agentnative.evidence.validator import validate_evidence
from agentnative.models import (
    ArtifactSummary,
    CheckResult,
    Evidence,
    Limitation,
    PublicReport,
    ScanReport,
    Target,
)
from agentnative.security.sanitize import Sanitizer


class SafeReportBuilder:
    """Build the only report model renderers are allowed to consume."""

    def __init__(self, sanitizer: Sanitizer | None = None) -> None:
        self.sanitizer = sanitizer or Sanitizer()

    def build(self, report: ScanReport) -> PublicReport:
        validate_evidence(report)
        return PublicReport(
            scan_id=report.scan_id,
            target=Target(
                raw=self.sanitizer.uri(report.target.raw),
                canonical=self.sanitizer.uri(report.target.canonical),
                kind=report.target.kind,
            ),
            started_at=report.started_at,
            completed_at=report.completed_at,
            version=report.version,
            check_set_version=report.check_set_version,
            execution_status=report.execution_status,
            results=[self._result(result) for result in report.results],
            artifacts=[ArtifactSummary.from_artifact(artifact) for artifact in report.artifacts],
            limitations=[self._limitation(item) for item in report.limitations],
            summary=report.summary(),
            domains=report.domain_summary(),
        )

    def _result(self, result: CheckResult) -> CheckResult:
        return CheckResult(
            check=result.check,
            status=result.status,
            explanation=self.sanitizer.text(result.explanation)[0],
            remediation=self.sanitizer.text(result.remediation)[0],
            confidence=result.confidence,
            evidence=[self._evidence(item) for item in result.evidence],
        )

    def _evidence(self, evidence: Evidence) -> Evidence:
        return Evidence(
            evidence_id=evidence.evidence_id,
            source_uri=self.sanitizer.uri(evidence.source_uri),
            artifact_type=evidence.artifact_type,
            acquisition_timestamp=evidence.acquisition_timestamp,
            content_hash=evidence.content_hash,
            artifact_id=evidence.artifact_id,
            check_id=evidence.check_id,
            relevant_fragment=self.sanitizer.text(evidence.relevant_fragment)[0],
            normalized_representation=self.sanitizer.value(evidence.normalized_representation),
            observation=self.sanitizer.text(evidence.observation)[0],
            confidence=evidence.confidence,
            redaction_status=evidence.redaction_status,
        )

    def _limitation(self, limitation: Limitation | str) -> Limitation:
        if isinstance(limitation, Limitation):
            return Limitation(
                code=self.sanitizer.text(limitation.code)[0],
                resource=self.sanitizer.uri(limitation.resource) if limitation.resource else None,
                reason=self.sanitizer.text(limitation.reason)[0],
            )
        return Limitation("UNSTRUCTURED_LIMITATION", None, self.sanitizer.text(str(limitation))[0])


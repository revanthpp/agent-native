from __future__ import annotations

from agentnative.models import ScanReport


class EvidenceIntegrityError(ValueError):
    pass


def validate_evidence(report: ScanReport) -> None:
    artifacts = {artifact.artifact_id: artifact for artifact in report.artifacts}
    by_uri = {artifact.uri: artifact for artifact in report.artifacts}
    seen: set[str] = set()
    for result in report.results:
        for evidence in result.evidence:
            if evidence.evidence_id in seen:
                raise EvidenceIntegrityError(f"duplicate evidence ID: {evidence.evidence_id}")
            seen.add(evidence.evidence_id)
            artifact = artifacts.get(evidence.artifact_id)
            if artifact is None:
                raise EvidenceIntegrityError(f"evidence references unknown artifact: {evidence.artifact_id}")
            if by_uri.get(evidence.source_uri) is not artifact:
                raise EvidenceIntegrityError(f"evidence URI does not match artifact: {evidence.evidence_id}")
            if evidence.content_hash != artifact.content_hash:
                raise EvidenceIntegrityError(f"evidence hash does not match artifact: {evidence.evidence_id}")
            if evidence.artifact_type != artifact.artifact_type:
                raise EvidenceIntegrityError(f"evidence type does not match artifact: {evidence.evidence_id}")

from __future__ import annotations

from agentnative.security.secrets import SecretDetector


class UnsafeReportError(RuntimeError):
    """Raised when final report output still contains detected sensitive material."""


def validate_output(output: str, detector: SecretDetector | None = None) -> None:
    detector = detector or SecretDetector()
    if detector.detect_text(output):
        # Never include matched text or offsets in this exception.
        raise UnsafeReportError("report output blocked by sensitive-content validation")


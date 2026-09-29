from enum import StrEnum


class EvidenceStatus(StrEnum):
    DECLARED = "DECLARED"
    OBSERVED = "OBSERVED"
    VERIFIED = "VERIFIED"
    NOT_OBSERVED = "NOT_OBSERVED"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID = "INVALID"


__all__ = ["EvidenceStatus"]

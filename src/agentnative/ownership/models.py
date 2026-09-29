from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Environment(StrEnum):
    SANDBOX = "SANDBOX"; STAGING = "STAGING"; PRODUCTION_READ_ONLY = "PRODUCTION_READ_ONLY"; PRODUCTION_ACTIVE = "PRODUCTION_ACTIVE"
class VerificationStatus(StrEnum): VERIFIED = "VERIFIED"; INVALID = "INVALID"; EXPIRED = "EXPIRED"
@dataclass(frozen=True)
class OwnershipVerification:
    verification_id: str; business_id: str; target: str; method: str; challenge_hash: str; verified_at: datetime; expires_at: datetime; environment: Environment; status: VerificationStatus; evidence: str
    def is_valid(self, now=None):
        from datetime import timezone
        return self.status == VerificationStatus.VERIFIED and (now or datetime.now(timezone.utc)) < self.expires_at

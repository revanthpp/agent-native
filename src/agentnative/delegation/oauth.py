from __future__ import annotations

from dataclasses import dataclass

from agentnative.identity.evidence import EvidenceStatus


@dataclass(frozen=True)
class OAuthFinding:
    control: str
    status: EvidenceStatus
    reason: str


def assess_oauth(metadata: dict[str, object]) -> list[OAuthFinding]:
    """Assess declared OAuth metadata without upgrading declaration to proof."""
    controls = ("authorization_metadata", "scopes", "audience", "redirect_uris", "pkce", "token_lifetime", "revocation", "sender_constrained")
    return [
        OAuthFinding(
            control,
            EvidenceStatus.DECLARED if control in metadata else EvidenceStatus.NOT_OBSERVED,
            "target metadata declares this property" if control in metadata else "no evidence observed",
        )
        for control in controls
    ]


__all__ = ["EvidenceStatus", "OAuthFinding", "assess_oauth"]

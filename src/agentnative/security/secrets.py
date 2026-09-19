from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from agentnative.security.canonicalize import SecretCanonicalizer


REDACTION_MARKER = "[REDACTED]"
_VALUE = r'(?P<value>"[A-Za-z0-9][A-Za-z0-9._~+/=%-]{3,}"|\'[A-Za-z0-9][A-Za-z0-9._~+/=%-]{3,}\'|[A-Za-z0-9][A-Za-z0-9._~+/=%-]{3,})'
_KEY = r'(?:api[_-]?key|apikey|token|access[_-]?token|secret|client[_-]?secret|password|passwd|session(?:[_-]?id)?|cookie)'


@dataclass(frozen=True)
class SecretMatch:
    """A non-sensitive description of a detected value.

    The match intentionally never stores the matched secret itself.
    """

    kind: str
    start: int
    end: int
    value_start: int
    field_path: str = ""
    variant_index: int = 0


class SecretDetector:
    """Canonical detector shared by AR-020, sanitization, and output checks."""

    _rules = (
        ("authorization_bearer", re.compile(rf"(?i)(?:\bAuthorization\s*[:=]\s*Bearer\s+){_VALUE}")),
        ("bearer_token", re.compile(rf"(?i)\bBearer\s+{_VALUE}")),
        ("credential_assignment", re.compile(rf"(?i)[\"']?\b{_KEY}\b[\"']?\s*[:=]\s*{_VALUE}")),
        ("prefixed_key", re.compile(rf"(?i)\b(?:x-)?{_KEY}\b\s*[:=]\s*{_VALUE}")),
        ("provider_key", re.compile(r"\b(?:sk|pk)_[A-Za-z0-9_-]{12,}\b")),
        ("long_encoded_value", re.compile(r"\b[A-Za-z0-9+/]{32,}={0,2}\b")),
    )
    _sensitive_keys = {
        "api_key", "apikey", "token", "access_token", "secret", "client_secret",
        "password", "passwd", "session", "session_id", "sessionid", "cookie",
    }
    _benign_values = {
        "budget", "budgeting", "management", "policy", "timeout", "documented",
        "example", "value", "control", "guidance", "testing", "bestpractice",
        "token", "credential", "authentication", "auth",
    }

    def __init__(self, canonicalizer: SecretCanonicalizer | None = None) -> None:
        self.canonicalizer = canonicalizer or SecretCanonicalizer()

    def detect(self, value: Any, field_path: str = "") -> list[SecretMatch]:
        if isinstance(value, str):
            return self.detect_text(value, field_path)
        if isinstance(value, Mapping):
            try:
                serialized = json.dumps(value, sort_keys=True, default=str)
            except (TypeError, ValueError):
                serialized = str(value)
            return self.detect_text(serialized, field_path)
        if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
            try:
                serialized = json.dumps(value, default=str)
            except (TypeError, ValueError):
                serialized = str(value)
            return self.detect_text(serialized, field_path)
        return []

    def detect_text(self, value: str, field_path: str = "") -> list[SecretMatch]:
        matches: list[SecretMatch] = []
        for variant_index, variant in enumerate(self.canonicalizer.variants(value)):
            for kind, pattern in self._rules:
                for match in pattern.finditer(variant):
                    if kind == "long_encoded_value" and re.fullmatch(r"[0-9a-fA-F]{32,}", match.group(0)):
                        # Public reports intentionally contain SHA-256 content hashes;
                        # only suppress a pure-hex value in an explicit hash field.
                        context = variant[max(0, match.start() - 48):match.start()]
                        if re.search(r"[\"'](?:content_hash|hash)[\"']\s*:\s*[\"']?$", context, re.I):
                            continue
                    if kind in {"authorization_bearer", "bearer_token", "credential_assignment", "prefixed_key"}:
                        candidate = match.group("value").strip("\"'").lower()
                        if candidate in self._benign_values:
                            continue
                    value_start = match.start("value") if "value" in pattern.groupindex else match.start()
                    matches.append(SecretMatch(kind, match.start(), match.end(), value_start, field_path, variant_index))
        unique = {(item.variant_index, item.start, item.end): item for item in matches}
        return sorted(unique.values(), key=lambda item: (item.start, item.end, item.kind))

    def is_sensitive_key(self, key: str) -> bool:
        normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
        return normalized in self._sensitive_keys

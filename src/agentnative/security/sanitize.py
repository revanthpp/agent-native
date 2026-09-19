from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import quote, unquote_plus, urlsplit, urlunsplit

from agentnative.security.secrets import REDACTION_MARKER, SecretDetector


ANSI_ESCAPE = re.compile(r"(?:\x1B\[[0-?]*[ -/]*[@-~]|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f])")


class Sanitizer:
    def __init__(self, detector: SecretDetector | None = None) -> None:
        self.detector = detector or SecretDetector()

    def text(self, value: str) -> tuple[str, bool]:
        matches = self.detector.detect_text(value)
        if not matches:
            return value, False
        sanitized = value
        raw_matches = [match for match in matches if match.variant_index == 0]
        if not raw_matches:
            return REDACTION_MARKER, True
        for match in sorted(raw_matches, key=lambda item: item.value_start, reverse=True):
            sanitized = sanitized[:match.value_start] + REDACTION_MARKER + sanitized[match.end:]
        return sanitized, True

    def value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.text(value)[0]
        if isinstance(value, Mapping):
            sanitized: dict[Any, Any] = {}
            for key, item in value.items():
                safe_key = self.value(key)
                if isinstance(key, str) and self.detector.is_sensitive_key(key) and isinstance(item, str) and self.detector.detect_text(f"{key}={item}"):
                    sanitized[safe_key] = REDACTION_MARKER
                else:
                    sanitized[safe_key] = self.value(item)
            return sanitized
        if isinstance(value, list):
            return [self.value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.value(item) for item in value)
        return value

    def uri(self, value: str) -> str:
        value = str(value)
        parsed = urlsplit(value)
        if not parsed.scheme or not parsed.netloc:
            return self.text(value)[0]
        hostname = parsed.hostname or ""
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        try:
            port = f":{parsed.port}" if parsed.port else ""
        except ValueError:
            port = ""
        query_parts: list[str] = []
        for part in parsed.query.split("&") if parsed.query else []:
            key, separator, raw_value = part.partition("=")
            decoded_key = unquote_plus(key)
            decoded_value = unquote_plus(raw_value)
            if separator and (self.detector.is_sensitive_key(decoded_key) or self.detector.detect_text(f"{decoded_key}={decoded_value}")):
                safe_value = REDACTION_MARKER
            else:
                safe_value = self.text(decoded_value)[0]
            query_parts.append(f"{key}={quote(safe_value, safe='-._~/[]')}" if separator else key)
        safe_query = "&".join(query_parts)
        safe = urlunsplit((parsed.scheme, hostname + port, self.text(parsed.path)[0], safe_query, self.text(parsed.fragment)[0]))
        return self.text(safe)[0]

    def terminal(self, value: str) -> str:
        return ANSI_ESCAPE.sub("", self.text(value)[0])


_DEFAULT = Sanitizer()


def redact(value: str) -> tuple[str, bool]:
    return _DEFAULT.text(value)


def sanitize_public_uri(value: str) -> str:
    return _DEFAULT.uri(value)


def sanitize_terminal(value: str) -> str:
    return _DEFAULT.terminal(value)

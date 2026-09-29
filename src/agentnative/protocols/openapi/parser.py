from __future__ import annotations

import json
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


class OpenAPIParseError(ValueError):
    """Safe, implementation-independent description of target parse failure."""

    def __init__(self, error_code: str, message: str, *, category: str = "TARGET_INPUT_INVALID") -> None:
        super().__init__(message)
        self.error_code = error_code
        self.category = category
        self.public_message = message


def load_openapi_document(document: str | bytes | dict[str, Any]) -> dict[str, Any]:
    if isinstance(document, dict):
        return document
    if not isinstance(document, (str, bytes)):
        raise OpenAPIParseError("OPENAPI_DOCUMENT_TYPE_INVALID", "OpenAPI document must be JSON, YAML, or an object")
    try:
        text = document.decode("utf-8") if isinstance(document, bytes) else document
    except UnicodeDecodeError as exc:
        raise OpenAPIParseError("OPENAPI_ENCODING_INVALID", "OpenAPI document is not valid UTF-8") from exc
    if len(text.encode("utf-8")) > 5_000_000:
        raise OpenAPIParseError("OPENAPI_DOCUMENT_TOO_LARGE", "document exceeds the 5 MiB parser limit", category="TARGET_INPUT_UNSUPPORTED")
    try: result = json.loads(text)
    except json.JSONDecodeError:
        if yaml is None:
            raise OpenAPIParseError("OPENAPI_YAML_UNSUPPORTED", "YAML parsing is not available", category="TARGET_INPUT_UNSUPPORTED")
        try:
            # safe_load never constructs Python objects. Unsupported/custom
            # tags are rejected and normalized below rather than executed.
            result = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise OpenAPIParseError("OPENAPI_YAML_PARSE_INVALID", "YAML document could not be safely parsed") from exc
    if not isinstance(result, dict):
        raise OpenAPIParseError("OPENAPI_DOCUMENT_OBJECT_REQUIRED", "OpenAPI document must be an object")
    return result


__all__ = ["OpenAPIParseError", "load_openapi_document"]

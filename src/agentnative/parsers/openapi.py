from __future__ import annotations

import json
from typing import Any

from agentnative.models import OpenAPIDocument, Operation


class OpenAPIParseError(ValueError):
    pass


def parse_openapi(content: str, uri: str) -> OpenAPIDocument:
    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        raise OpenAPIParseError("v1.0 accepts JSON OpenAPI documents; YAML support is intentionally deferred") from exc
    if not isinstance(raw, dict) or not (raw.get("openapi") or raw.get("swagger")):
        raise OpenAPIParseError("document does not declare OpenAPI or Swagger")
    paths = raw.get("paths")
    if not isinstance(paths, dict):
        raise OpenAPIParseError("OpenAPI document has no valid paths object")
    components = raw.get("components") if isinstance(raw.get("components"), dict) else {}
    schemes = components.get("securitySchemes") if isinstance(components.get("securitySchemes"), dict) else {}
    operations: list[Operation] = []
    for path, path_item in paths.items():
        if not isinstance(path, str) or not isinstance(path_item, dict):
            continue
        common_parameters = path_item.get("parameters") if isinstance(path_item.get("parameters"), list) else []
        for method, operation_data in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "head", "options", "trace"}:
                continue
            if not isinstance(operation_data, dict):
                continue
            parameters = [item for item in common_parameters + (operation_data.get("parameters") or []) if isinstance(item, dict)]
            extensions = {key: value for key, value in operation_data.items() if key.startswith("x-")}
            operations.append(
                Operation(
                    operation_id=str(operation_data.get("operationId") or ""),
                    method=method.upper(),
                    path=path,
                    summary=str(operation_data.get("summary") or ""),
                    description=str(operation_data.get("description") or ""),
                    parameters=parameters,
                    request_body=operation_data.get("requestBody") if isinstance(operation_data.get("requestBody"), dict) else None,
                    responses=operation_data.get("responses") if isinstance(operation_data.get("responses"), dict) else {},
                    security=operation_data.get("security") if isinstance(operation_data.get("security"), list) else [],
                    extensions=extensions,
                    source_uri=uri,
                )
            )
    return OpenAPIDocument(
        uri=uri,
        version=str(raw.get("info", {}).get("version")) if isinstance(raw.get("info"), dict) and raw.get("info", {}).get("version") is not None else None,
        title=str(raw.get("info", {}).get("title")) if isinstance(raw.get("info"), dict) and raw.get("info", {}).get("title") is not None else None,
        security_schemes=schemes,
        operations=operations,
        raw=raw,
    )

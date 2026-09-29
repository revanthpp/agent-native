from __future__ import annotations

import hashlib
import json
from typing import Any

import yaml

from agentnative.capabilities.models import Capability
from agentnative.protocols.base import ProtocolAdapter
from agentnative.protocols.models import ActionClass, AdapterResult, EvidenceRef, Limitation, ProtocolArtifact, SideEffect
from agentnative.protocols.openapi.parser import OpenAPIParseError, load_openapi_document
from agentnative.protocols.openapi.refs import SafeRefResolver


class OpenAPIAdapter(ProtocolAdapter):
    protocol_family = "OPENAPI"
    protocol_version = "3.x"

    @staticmethod
    def _content_hash(document: Any) -> str:
        """Hash input without retaining or rendering target-controlled content."""

        if isinstance(document, bytes):
            payload = document
        elif isinstance(document, str):
            payload = document.encode("utf-8", errors="replace")
        elif isinstance(document, dict):
            try:
                payload = json.dumps(document, sort_keys=True, default=lambda _: "<opaque>").encode("utf-8")
            except (TypeError, ValueError, RecursionError):
                payload = b"opaque-dict"
        else:
            payload = type(document).__name__.encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _artifact(self, document: Any, uri: str) -> ProtocolArtifact:
        return ProtocolArtifact(uri, "openapi", self._content_hash(document))

    def _parse_document(self, document: Any) -> dict[str, Any]:
        """Single parser seam; kept explicit for boundary and mutation tests."""

        return load_openapi_document(document)

    def _error_result(self, document: Any, uri: str, *, code: str, category: str, message: str, operation: str) -> AdapterResult:
        artifact = self._artifact(document, uri)
        result = AdapterResult(
            "OPENAPI",
            "unknown",
            self.adapter_version,
            "structural",
            artifacts=[artifact],
            detected=False,
            validity={"TARGET_INPUT_INVALID": "INVALID", "TARGET_INPUT_UNSUPPORTED": "UNSUPPORTED"}.get(category, "ERROR"),
        )
        result.add_error(code, message, category=category, operation=operation, artifact=artifact)
        return result

    def _normalize_parse_error(self, document: Any, uri: str, exc: ValueError | yaml.YAMLError, *, operation: str) -> AdapterResult:
        """Map known parser failures to stable Agent Native error evidence."""

        if isinstance(exc, OpenAPIParseError):
            code, category, message = exc.error_code, exc.category, exc.public_message
        elif isinstance(exc, yaml.YAMLError):
            code, category, message = "OPENAPI_YAML_PARSE_INVALID", "TARGET_INPUT_INVALID", "YAML document could not be safely parsed"
        elif isinstance(exc, UnicodeDecodeError):
            code, category, message = "OPENAPI_ENCODING_INVALID", "TARGET_INPUT_INVALID", "OpenAPI document is not valid UTF-8"
        elif isinstance(exc, json.JSONDecodeError):
            code, category, message = "OPENAPI_JSON_PARSE_INVALID", "TARGET_INPUT_INVALID", "JSON document could not be parsed"
        else:
            code, category, message = "OPENAPI_DOCUMENT_INVALID", "TARGET_INPUT_INVALID", "OpenAPI document could not be parsed"
        return self._error_result(document, uri, code=code, category=category, message=message, operation=operation)

    def detect(self, document: Any) -> bool:
        try:
            raw = self._parse_document(document)
        except (ValueError, yaml.YAMLError):
            return False
        return "openapi" in raw or "swagger" in raw

    def parse(self, document: Any, uri: str = "memory://openapi", *, fetch=None, enforce_network_policy: bool = True) -> AdapterResult:
        try:
            raw = self._parse_document(document)
        except (ValueError, yaml.YAMLError) as exc:
            return self._normalize_parse_error(document, uri, exc, operation="parse")

        artifact = self._artifact(document, uri)
        declared_version = raw.get("openapi") or raw.get("swagger")
        version = declared_version if isinstance(declared_version, str) else "unknown"
        result = AdapterResult("OPENAPI", version, self.adapter_version, "structural", artifacts=[artifact])
        result.detected = "openapi" in raw or "swagger" in raw
        if not result.detected:
            result.validity = "NOT_DETECTED"
            return result

        result.validity = "VALID" if version.startswith(("3.0.", "3.1.", "3.2.")) else "UNSUPPORTED"
        if result.validity == "UNSUPPORTED":
            result.limitations.append(Limitation("OAS_VERSION_UNSUPPORTED", f"unsupported OpenAPI version {version}", uri))

        paths = raw.get("paths")
        if not isinstance(paths, dict):
            result.validity = "INVALID"
            result.add_error("OPENAPI_PATHS_INVALID", "OpenAPI document has no valid paths object", artifact=artifact)
            return result

        try:
            refs = SafeRefResolver(raw, uri, fetch, enforce_network_policy=enforce_network_policy)
        except ValueError:
            result.validity = "INVALID"
            result.add_error("OPENAPI_REFERENCE_URI_INVALID", "OpenAPI reference base URI is invalid", artifact=artifact)
            return result

        components = raw.get("components") if isinstance(raw.get("components"), dict) else {}
        security_schemes = components.get("securitySchemes") if isinstance(components.get("securitySchemes"), dict) else {}
        for name, scheme in security_schemes.items():
            if isinstance(name, str) and isinstance(scheme, dict):
                result.auth_requirements.append({"name": name, **scheme})

        for path, item in paths.items():
            if not isinstance(path, str) or not isinstance(item, dict):
                result.limitations.append(Limitation("OAS_INVALID_PATH_ITEM", "path item must be an object", str(path)[:128]))
                continue
            for method, operation in item.items():
                if not isinstance(method, str) or method.lower() not in {"get", "post", "put", "patch", "delete", "head", "options", "trace"}:
                    continue
                if not isinstance(operation, dict):
                    result.validity = "INVALID"
                    result.add_error("OPENAPI_OPERATION_INVALID", "OpenAPI operation must be an object", artifact=artifact, sanitized_details={"path": path[:128], "method": method[:32]})
                    continue
                pointer = f"#/paths/{path}/{method}"
                try:
                    op = refs.resolve(operation, pointer=pointer)
                except (KeyError, TypeError, ValueError):
                    result.validity = "INVALID"
                    result.add_error("OPENAPI_REFERENCE_RESOLUTION_INVALID", "OpenAPI reference could not be resolved safely", artifact=artifact, sanitized_details={"pointer": pointer[:256]})
                    continue
                if not isinstance(op, dict):
                    result.validity = "INVALID"
                    result.add_error("OPENAPI_OPERATION_INVALID", "Resolved OpenAPI operation is not an object", artifact=artifact, sanitized_details={"pointer": pointer[:256]})
                    continue
                name = str(op.get("operationId") or f"{method.upper()} {path}")
                description = str(op.get("description") or op.get("summary") or "")
                lower = f"{name} {description}".lower()
                if method.upper() in {"GET", "HEAD", "OPTIONS"}:
                    action, effect = ActionClass.READ, SideEffect.NONE
                elif method.upper() == "DELETE":
                    action, effect = ActionClass.DELETE, SideEffect.IRREVERSIBLE
                elif method.upper() in {"PUT", "PATCH"}:
                    action, effect = ActionClass.UPDATE, SideEffect.REVERSIBLE
                elif "preview" in lower or "quote" in lower:
                    action, effect = ActionClass.PREVIEW, SideEffect.NONE
                else:
                    action, effect = ActionClass.CREATE, SideEffect.UNKNOWN
                security = op.get("security") if isinstance(op.get("security"), list) else []
                scopes = sorted({scope for entry in security if isinstance(entry, dict) for values in entry.values() if isinstance(values, list) for scope in values if isinstance(scope, str)})
                result.capabilities.append(
                    Capability(
                        f"openapi:{name}",
                        "unknown",
                        name,
                        description,
                        [uri],
                        action,
                        input_schema=op.get("requestBody") if isinstance(op.get("requestBody"), dict) else {},
                        output_schema=op.get("responses") if isinstance(op.get("responses"), dict) else {},
                        required_scopes=scopes,
                        side_effect=effect,
                        evidence_refs=[EvidenceRef(uri, pointer, "openapi-operation")],
                    )
                )

        result.limitations.extend(refs.limitations)
        result.artifacts.extend(refs.artifacts)
        return result

    def validate(self, document: Any) -> list[str]:
        return self.parse(document).errors

    def normalize(self, document: Any, uri: str = "memory://openapi") -> AdapterResult:
        return self.parse(document, uri)

    def enumerate_auth_requirements(self, document: Any, uri: str = "memory://openapi") -> list[dict[str, Any]]:
        return self.parse(document, uri).auth_requirements

    def enumerate_actions(self, document: Any, uri: str = "memory://openapi") -> list[Any]:
        return self.parse(document, uri).capabilities

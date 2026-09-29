from __future__ import annotations

import json
from typing import Any

from agentnative.protocols.base import ProtocolAdapter
from agentnative.capabilities.models import Capability
from agentnative.protocols.models import ActionClass, AdapterResult, EvidenceRef, Limitation, ProtocolArtifact, SideEffect


class MCPAdapter(ProtocolAdapter):
    protocol_family = "MCP"; protocol_version = "2026-07-28"

    def detect(self, document: Any) -> bool: return isinstance(document, dict) and any(key in document for key in ("tools", "resources", "prompts"))

    def parse(self, document: Any, uri: str = "memory://mcp") -> AdapterResult:
        result = AdapterResult("MCP", self.protocol_version, self.adapter_version, "declared-surface", [ProtocolArtifact(uri, "mcp-surface")]); result.detected = self.detect(document)
        if not isinstance(document, dict) or not result.detected:
            result.validity = "NOT_DETECTED"
            return result
        for key in ("tools", "resources", "prompts"):
            if key in document and not isinstance(document[key], (list, dict)): result.limitations.append(Limitation("MCP_INVALID_INVENTORY", f"{key} inventory is not a list/object", f"/{key}"))
        tools = document.get("tools", []); tools = ([{"name": key, **value} if isinstance(value, dict) else {"name": key} for key, value in tools.items()] if isinstance(tools, dict) else tools)
        if not isinstance(tools, list):
            result.validity = "INVALID"
            result.add_error("MCP_TOOLS_INVALID", "MCP tools inventory must be a list or object", artifact=result.artifacts[0])
            return result
        seen_tools: set[str] = set()
        for index, tool in enumerate(tools):
            if not isinstance(tool, dict) or not isinstance(tool.get("name"), str): result.limitations.append(Limitation("MCP_INVALID_TOOL", "tool must have a string name", f"/tools/{index}")); continue
            name, description = tool["name"], str(tool.get("description") or ""); lower = f"{name} {description}".lower(); destructive = any(word in lower for word in ("delete", "destroy", "purchase", "transfer", "refund"))
            if name in seen_tools: result.limitations.append(Limitation("MCP_DUPLICATE_TOOL", "tool identifier is duplicated", f"/tools/{index}"))
            seen_tools.add(name)
            if "inputSchema" in tool and not isinstance(tool["inputSchema"], dict): result.limitations.append(Limitation("MCP_INVALID_INPUT_SCHEMA", "inputSchema must be an object", f"/tools/{index}"))
            if "outputSchema" in tool and not isinstance(tool["outputSchema"], dict): result.limitations.append(Limitation("MCP_INVALID_OUTPUT_SCHEMA", "outputSchema must be an object", f"/tools/{index}"))
            if len(json.dumps(tool, default=str)) > 1_000_000: result.limitations.append(Limitation("MCP_SCHEMA_SIZE", "tool declaration exceeds 1 MiB", f"/tools/{index}"))
            if destructive and "read-only" in lower: result.limitations.append(Limitation("MCP_DECLARATION_CONTRADICTION", "destructive structure cannot be downgraded by prose", f"/tools/{index}"))
            if "ignore previous" in lower or "system prompt" in lower: result.limitations.append(Limitation("MCP_UNTRUSTED_INSTRUCTION_TEXT", "tool description contains instruction-like text and is treated as data", f"/tools/{index}"))
            result.capabilities.append(Capability(f"mcp:{name}", "unknown", name, description, [uri], ActionClass.CREATE if destructive else ActionClass.READ, input_schema=tool.get("inputSchema") if isinstance(tool.get("inputSchema"), dict) else {}, output_schema=tool.get("outputSchema") if isinstance(tool.get("outputSchema"), dict) else {}, side_effect=SideEffect.IRREVERSIBLE if destructive else SideEffect.UNKNOWN, evidence_refs=[EvidenceRef(uri, f"/tools/{index}", "mcp-tool", .9)]))
        resources = document.get("resources", [])
        resources = ([{"name": key, **value} if isinstance(value, dict) else {"name": key} for key, value in resources.items()] if isinstance(resources, dict) else resources)
        if isinstance(resources, list):
            for index, resource in enumerate(resources):
                if not isinstance(resource, dict) or not isinstance(resource.get("uri") or resource.get("name"), str):
                    result.limitations.append(Limitation("MCP_INVALID_RESOURCE", "resource must have a uri or name", f"/resources/{index}")); continue
                name = str(resource.get("name") or resource.get("uri")); description = str(resource.get("description") or "")
                result.capabilities.append(Capability(f"mcp:resource:{name}", "unknown", name, description, [uri], ActionClass.READ, side_effect=SideEffect.NONE, evidence_refs=[EvidenceRef(uri, f"/resources/{index}", "mcp-resource", .9)]))
        prompts = document.get("prompts", [])
        prompts = ([{"name": key, **value} if isinstance(value, dict) else {"name": key} for key, value in prompts.items()] if isinstance(prompts, dict) else prompts)
        if isinstance(prompts, list):
            for index, prompt in enumerate(prompts):
                if not isinstance(prompt, dict) or not isinstance(prompt.get("name"), str):
                    result.limitations.append(Limitation("MCP_INVALID_PROMPT", "prompt must have a string name", f"/prompts/{index}")); continue
                name = prompt["name"]; description = str(prompt.get("description") or "")
                result.capabilities.append(Capability(f"mcp:prompt:{name}", "unknown", name, description, [uri], ActionClass.RECOMMEND, side_effect=SideEffect.NONE, evidence_refs=[EvidenceRef(uri, f"/prompts/{index}", "mcp-prompt", .9)]))
        if document.get("extensions"): result.limitations.append(Limitation("MCP_UNKNOWN_EXTENSIONS", "extensions are not executed or trusted", "/extensions"))
        auth_keys = ("auth", "authorization", "authentication")
        auth_key = next((key for key in auth_keys if key in document), None)
        if auth_key is not None:
            auth = document[auth_key]
            if isinstance(auth, dict):
                result.auth_requirements.append(auth)
            else:
                result.limitations.append(Limitation("MCP_INVALID_AUTH", "authentication declaration must be an object", f"/{auth_key}"))
        result.validity = "VALID_WITH_WARNINGS" if result.limitations else "VALID"; return result

    def validate(self, document: Any) -> list[str]: return self.parse(document).errors
    def normalize(self, document: Any, uri: str = "memory://mcp") -> AdapterResult: return self.parse(document, uri)
    def enumerate_auth_requirements(self, document: Any, uri: str = "memory://mcp") -> list[dict[str, Any]]: return self.parse(document, uri).auth_requirements
    def enumerate_actions(self, document: Any, uri: str = "memory://mcp") -> list[Any]: return self.parse(document, uri).capabilities

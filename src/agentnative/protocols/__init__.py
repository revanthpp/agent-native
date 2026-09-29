"""Canonical protocol APIs with lazy adapter imports to keep model modules acyclic."""
from importlib import import_module

from agentnative.protocols.base import ProtocolAdapter
from agentnative.protocols.models import AdapterError, AdapterResult
from agentnative.protocols.registry import AdapterRegistry

_LAZY = {
    "OpenAPIAdapter": ("agentnative.protocols.openapi.adapter", "OpenAPIAdapter"),
    "MCPAdapter": ("agentnative.protocols.mcp.adapter", "MCPAdapter"),
    "A2AAdapter": ("agentnative.protocols.a2a.adapter", "A2AAdapter"),
}


def __getattr__(name: str):
    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(name)
    module = import_module(target[0])
    value = getattr(module, target[1])
    globals()[name] = value
    return value


__all__ = ["AdapterError", "AdapterRegistry", "AdapterResult", "ProtocolAdapter", "OpenAPIAdapter", "MCPAdapter", "A2AAdapter"]

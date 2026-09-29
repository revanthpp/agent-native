from __future__ import annotations

from agentnative.protocols.base import ProtocolAdapter
from agentnative.protocols.models import AdapterResult, Limitation, ProtocolArtifact


class AdapterRegistry:
    def __init__(self, adapters: list[ProtocolAdapter] | None = None) -> None: self.adapters = adapters or []
    def register(self, adapter: ProtocolAdapter) -> None: self.adapters.append(adapter)
    def analyze(self, documents: list[tuple[object, str]]) -> list[AdapterResult]:
        results = []
        for adapter in self.adapters:
            for document, uri in documents:
                try:
                    if adapter.detect(document):
                        results.append(adapter.normalize(document, uri))
                        continue
                    # Give a non-detecting adapter one safe diagnostic pass so
                    # malformed candidate artifacts are not hidden. Adapters
                    # return NOT_DETECTED for unrelated, well-formed inputs.
                    candidate = adapter.normalize(document, uri)
                    if candidate.validity in {"INVALID", "ERROR"}:
                        results.append(candidate)
                except Exception as exc:
                    artifact = ProtocolArtifact(uri, adapter.protocol_family.lower())
                    result = AdapterResult(adapter.protocol_family, adapter.protocol_version, adapter.adapter_version, "error", artifacts=[artifact], validity="ERROR")
                    result.limitations.append(Limitation("ADAPTER_FAILURE", "adapter execution failed; see structured error evidence", uri))
                    result.add_error(
                        "ADAPTER_INTERNAL_ERROR",
                        "protocol adapter encountered an internal error",
                        category="ADAPTER_INTERNAL_ERROR",
                        operation="analyze",
                        artifact=artifact,
                        sanitized_details={"exception_type": type(exc).__name__},
                    )
                    results.append(result)
        return results

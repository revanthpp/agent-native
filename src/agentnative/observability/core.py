from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from agentnative.security.sanitize import Sanitizer


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    correlation_id: str
    parent_span_id: str | None = None

    @classmethod
    def new(cls, correlation_id: str | None = None) -> "TraceContext":
        trace = uuid4().hex
        return cls(trace, correlation_id or trace)

    def child(self) -> "TraceContext":
        return TraceContext(self.trace_id, self.correlation_id, uuid4().hex[:16])


@dataclass(frozen=True)
class TraceEvent:
    name: str
    timestamp: str
    trace_id: str
    span_id: str
    correlation_id: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "correlation_id": self.correlation_id,
            "attributes": Sanitizer().value(self.attributes),
        }


class TraceRecorder:
    def __init__(self, context: TraceContext, *, common_attributes: dict[str, Any] | None = None) -> None:
        self.context = context
        self.common_attributes = dict(common_attributes or {})
        self.events: list[TraceEvent] = []

    def emit(self, name: str, attributes: dict[str, Any] | None = None) -> TraceEvent:
        merged = {**self.common_attributes, **(attributes or {})}
        event = TraceEvent(name, _timestamp(), self.context.trace_id, uuid4().hex[:16], self.context.correlation_id, merged)
        self.events.append(event)
        return event

    def export(self) -> dict[str, Any]:
        events = [event.to_dict() for event in self.events]
        return {
            "trace_id": self.context.trace_id,
            "correlation_id": self.context.correlation_id,
            "events": events,
            "otel": {
                "resourceSpans": [{
                    "scopeSpans": [{
                        "spans": [
                            {
                                "traceId": event.trace_id,
                                "spanId": event.span_id,
                                "name": event.name,
                                "startTime": event.timestamp,
                                "attributes": [{"key": key, "value": {"stringValue": str(value)}} for key, value in events[index]["attributes"].items() if value is not None],
                                "events": [{"name": event.name, "time": event.timestamp}],
                            }
                            for index, event in enumerate(self.events)
                        ]
                    }]
                }]
            },
        }

    def has_event(self, name: str) -> bool:
        return any(event.name == name for event in self.events)


__all__ = ["TraceContext", "TraceEvent", "TraceRecorder"]

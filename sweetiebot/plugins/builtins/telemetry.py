from __future__ import annotations

from typing import Dict, List

from sweetiebot.plugins.base import TelemetrySinkPlugin
from sweetiebot.telemetry.models import TraceEvent


class InMemoryTelemetrySinkPlugin(TelemetrySinkPlugin):
    plugin_id = "sweetiebot.telemetry.inmemory"

    def __init__(self) -> None:
        self.events: List[TraceEvent] = []
        self.config = {}

    def manifest(self) -> Dict[str, object]:
        base = super().manifest()
        base.capabilities = ["emit", "recent_events"]
        return base

    def emit(self, event: TraceEvent) -> TraceEvent:
        self.events.append(event)
        return event

    def recent_events(self, limit: int = 25) -> List[TraceEvent]:
        return list(reversed(self.events[-limit:]))

    def healthcheck(self) -> Dict[str, object]:
        return {
            "healthy": True,
            "plugin_id": self.plugin_id,
            "events": len(self.events),
        }

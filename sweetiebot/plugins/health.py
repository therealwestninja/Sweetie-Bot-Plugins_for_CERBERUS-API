from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class PluginHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class PluginHealthCheck:
    plugin_id: str
    status: PluginHealthStatus = PluginHealthStatus.UNKNOWN
    summary: str = "No health information reported."
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "status": self.status.value,
            "summary": self.summary,
            "details": dict(self.details),
            "warnings": list(self.warnings),
        }


def coerce_health_status(value: Any) -> PluginHealthStatus:
    if isinstance(value, PluginHealthStatus):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for item in PluginHealthStatus:
            if item.value == normalized:
                return item
    return PluginHealthStatus.UNKNOWN

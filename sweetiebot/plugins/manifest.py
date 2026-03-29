from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .types import PluginFamily


@dataclass(slots=True)
class PluginManifest:
    plugin_id: str
    family: PluginFamily
    version: str = "0.1.0"
    display_name: Optional[str] = None
    description: str = ""
    priority: int = 100
    capabilities: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    supports_degraded_mode: bool = True
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "family": self.family.value,
            "version": self.version,
            "display_name": self.display_name or self.plugin_id,
            "description": self.description,
            "priority": self.priority,
            "capabilities": list(self.capabilities),
            "config_schema": dict(self.config_schema),
            "supports_degraded_mode": self.supports_degraded_mode,
            "dependencies": list(self.dependencies),
        }

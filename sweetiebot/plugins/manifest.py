from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sweetiebot.plugins.types import PluginType


@dataclass(slots=True)
class PluginManifest:
    plugin_id: str
    plugin_type: PluginType
    version: str = "0.1.0"
    display_name: str | None = None
    description: str = ""
    priority: int = 100
    capabilities: List[str] = field(default_factory=list)
    built_in: bool = True
    config_schema: Dict[str, Any] = field(default_factory=dict)

    @property
    def family(self) -> PluginType:
        return self.plugin_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_type": self.plugin_type.value,
            "family": self.plugin_type.value,
            "version": self.version,
            "display_name": self.display_name or self.plugin_id,
            "description": self.description,
            "priority": self.priority,
            "built_in": self.built_in,
            "capabilities": list(self.capabilities),
            "config_schema": dict(self.config_schema),
        }

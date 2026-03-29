from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from sweetiebot.plugins.types import PluginType


@dataclass(slots=True)
class PluginManifest:
    plugin_id: str
    plugin_type: PluginType
    version: str = "0.1.0"
    display_name: str | None = None
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    priority: int = 100
    dependencies: list[str] = field(default_factory=list)
    supports_degraded_mode: bool = True
    author: str | None = None
    homepage: str | None = None
    entry_point: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["plugin_type"] = self.plugin_type.value
        return payload


@dataclass(slots=True)
class PluginHealth:
    ok: bool = True
    status: str = "ok"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

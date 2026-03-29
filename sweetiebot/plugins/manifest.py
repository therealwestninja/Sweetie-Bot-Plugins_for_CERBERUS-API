from __future__ import annotations

from pydantic import BaseModel, Field

from sweetiebot.plugins.types import PluginType


class PluginManifest(BaseModel):
    plugin_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    plugin_type: PluginType
    version: str = Field(default="0.1.0")
    priority: int = 100
    built_in: bool = False
    description: str = ""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from sweetiebot.plugins.base import BasePlugin, MemoryStorePlugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, BasePlugin] = {}

    def register(self, plugin: BasePlugin) -> None:
        self._plugins[plugin.plugin_id] = plugin

    def get(self, plugin_id: str) -> Optional[BasePlugin]:
        return self._plugins.get(plugin_id)

    def all(self) -> List[BasePlugin]:
        return list(self._plugins.values())

    def get_by_type(self, plugin_type: str) -> List[BasePlugin]:
        return [p for p in self._plugins.values() if getattr(p, "plugin_type", None) == plugin_type]

    def get_memory_store(self) -> Optional[MemoryStorePlugin]:
        stores = self.get_by_type("memory_store")
        return stores[0] if stores else None

    def plugin_summary(self) -> Dict[str, object]:
        return {
            "count": len(self._plugins),
            "plugin_ids": sorted(self._plugins.keys()),
            "types": sorted({getattr(p, "plugin_type", "unknown") for p in self._plugins.values()}),
        }

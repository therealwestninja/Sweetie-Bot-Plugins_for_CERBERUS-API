from __future__ import annotations

from collections import defaultdict
from importlib.metadata import entry_points
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Sequence, Type

from .base import BasePlugin
from .health import PluginHealthCheck, PluginHealthStatus, coerce_health_status
from .manifest import PluginManifest
from .types import PluginFamily


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: DefaultDict[PluginFamily, List[BasePlugin]] = defaultdict(list)

    def register(self, plugin: BasePlugin) -> None:
        manifest = plugin.manifest()
        self._plugins[manifest.family].append(plugin)
        self._plugins[manifest.family].sort(key=lambda p: p.manifest().priority)

    def get_plugins(self, family: PluginFamily) -> List[BasePlugin]:
        return list(self._plugins.get(family, []))

    def get_primary(self, family: PluginFamily) -> Optional[BasePlugin]:
        plugins = self.get_plugins(family)
        return plugins[0] if plugins else None

    def configure_from_mapping(self, mapping: Dict[str, Dict[str, Any]]) -> None:
        for family_plugins in self._plugins.values():
            for plugin in family_plugins:
                plugin_id = plugin.manifest().plugin_id
                if plugin_id in mapping:
                    plugin.configure(mapping[plugin_id])

    def load_entry_points(self, group: str = "sweetiebot.plugins") -> List[str]:
        loaded: List[str] = []
        try:
            discovered = entry_points()
            candidates = discovered.select(group=group) if hasattr(discovered, "select") else discovered.get(group, [])
        except Exception:
            return loaded

        for ep in candidates:
            plugin_cls = ep.load()
            plugin = plugin_cls()
            self.register(plugin)
            loaded.append(plugin.manifest().plugin_id)
        return loaded

    def summary(self) -> Dict[str, List[Dict[str, Any]]]:
        result: Dict[str, List[Dict[str, Any]]] = {}
        for family, plugins in self._plugins.items():
            result[family.value] = [plugin.manifest().to_dict() for plugin in plugins]
        return result

    def health_summary(self) -> Dict[str, Any]:
        families: Dict[str, List[Dict[str, Any]]] = {}
        counts = {
            "healthy": 0,
            "degraded": 0,
            "failed": 0,
            "disabled": 0,
            "unknown": 0,
            "total": 0,
        }

        for family, plugins in self._plugins.items():
            entries: List[Dict[str, Any]] = []
            for plugin in plugins:
                manifest = plugin.manifest().to_dict()
                health = plugin.healthcheck().to_dict()
                status = health["status"]
                counts[status] = counts.get(status, 0) + 1
                counts["total"] += 1
                entries.append({
                    "manifest": manifest,
                    "health": health,
                })
            families[family.value] = entries

        overall = "healthy"
        if counts["failed"] > 0:
            overall = "failed"
        elif counts["degraded"] > 0:
            overall = "degraded"
        elif counts["unknown"] > 0:
            overall = "unknown"

        return {
            "overall_status": overall,
            "counts": counts,
            "families": families,
        }

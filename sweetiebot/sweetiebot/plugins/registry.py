from __future__ import annotations

from typing import Dict, List, Optional

from sweetiebot.plugins.base import (
    AttentionStrategyPlugin,
    BasePlugin,
    DialogueProviderPlugin,
    EmoteMapperPlugin,
    MemoryStorePlugin,
    PerceptionSourcePlugin,
    TelemetrySinkPlugin,
)


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

    def get_telemetry_sink(self) -> Optional[TelemetrySinkPlugin]:
        sinks = self.get_by_type("telemetry_sink")
        return sinks[0] if sinks else None

    def get_attention_strategy(self) -> Optional[AttentionStrategyPlugin]:
        strategies = self.get_by_type("attention_strategy")
        return strategies[0] if strategies else None

    def get_perception_sources(self) -> List[PerceptionSourcePlugin]:
        return [p for p in self.get_by_type("perception_source") if isinstance(p, PerceptionSourcePlugin)]

    def get_dialogue_provider(self) -> Optional[DialogueProviderPlugin]:
        providers = self.get_by_type("dialogue_provider")
        return providers[0] if providers else None

    def get_emote_mapper(self) -> Optional[EmoteMapperPlugin]:
        mappers = self.get_by_type("emote_mapper")
        return mappers[0] if mappers else None

    def plugin_summary(self) -> Dict[str, object]:
        return {
            "count": len(self._plugins),
            "plugin_ids": sorted(self._plugins.keys()),
            "types": sorted({getattr(p, "plugin_type", "unknown") for p in self._plugins.values()}),
        }

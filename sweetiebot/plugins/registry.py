from __future__ import annotations

from typing import Any, Dict, List, Optional

from sweetiebot.dialogue.contracts import DialogueReply
from sweetiebot.plugins.base import BasePlugin, PluginError
from sweetiebot.plugins.builtins import (
    DefaultSafetyPolicyPlugin,
    DemoRoutinePackPlugin,
    InMemoryStorePlugin,
    InMemoryTelemetrySinkPlugin,
    LocalDialogueProviderPlugin,
    MockAudioOutputPlugin,
    MockPerceptionSourcePlugin,
    MockTTSProviderPlugin,
    RuleBasedAttentionStrategyPlugin,
)
from sweetiebot.plugins.config import load_plugin_config
from sweetiebot.plugins.health import summarize_plugin_health
from sweetiebot.plugins.types import PluginType


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, BasePlugin] = {}

    def register(self, plugin: BasePlugin) -> None:
        plugin_id = getattr(plugin, "plugin_id", None) or plugin.manifest().plugin_id
        if plugin_id in self._plugins:
            raise PluginError(f"Duplicate plugin id: {plugin_id}")
        self._plugins[plugin_id] = plugin

    def register_builtins(self) -> None:
        for plugin in [
            LocalDialogueProviderPlugin(),
            DemoRoutinePackPlugin(),
            DefaultSafetyPolicyPlugin(),
            InMemoryStorePlugin(),
            MockPerceptionSourcePlugin(),
            RuleBasedAttentionStrategyPlugin(),
            InMemoryTelemetrySinkPlugin(),
            MockTTSProviderPlugin(),
            MockAudioOutputPlugin(),
        ]:
            if plugin.plugin_id not in self._plugins:
                self.register(plugin)

    def get(self, plugin_id: str) -> Optional[BasePlugin]:
        return self._plugins.get(plugin_id)

    def plugins(self) -> List[BasePlugin]:
        return list(self._plugins.values())

    def all(self) -> List[BasePlugin]:
        return self.plugins()

    def _manifest_attr(self, plugin: BasePlugin, attr: str) -> Any:
        manifest = plugin.manifest()
        if hasattr(manifest, attr):
            return getattr(manifest, attr)
        if isinstance(manifest, dict):
            return manifest.get(attr)
        return None

    def _priority(self, plugin: BasePlugin) -> int:
        priority = self._manifest_attr(plugin, "priority")
        return int(priority if priority is not None else getattr(plugin, "priority", 100))

    def get_by_type(self, plugin_type: str | PluginType) -> List[BasePlugin]:
        value = plugin_type.value if isinstance(plugin_type, PluginType) else str(plugin_type)
        items = []
        for plugin in self._plugins.values():
            ptype = self._manifest_attr(plugin, "plugin_type") or getattr(plugin, "plugin_type", "")
            pvalue = ptype.value if hasattr(ptype, "value") else str(ptype)
            if pvalue == value:
                items.append(plugin)
        return sorted(items, key=self._priority)

    def list_ids_for_type(self, plugin_type: str | PluginType) -> List[str]:
        return [self._manifest_attr(p, "plugin_id") or p.plugin_id for p in self.get_by_type(plugin_type)]

    def list_all(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for plugin in self.plugins():
            manifest = plugin.manifest()
            manifest_payload = manifest.to_dict() if hasattr(manifest, "to_dict") else dict(manifest)
            health = plugin.healthcheck()
            if hasattr(health, "to_dict"):
                health = health.to_dict()
            elif isinstance(health, dict):
                health = dict(health)
                if "healthy" in health and "ok" not in health:
                    health["ok"] = bool(health["healthy"])
                    health.setdefault("status", "healthy" if health["ok"] else "error")
                    details = {k: v for k, v in health.items() if k not in {"healthy", "ok", "status", "plugin_id"}}
                    health["details"] = health.get("details", details)
            items.append({**manifest_payload, "health": health})
        return sorted(items, key=lambda item: (item.get("plugin_type", ""), item.get("priority", 100), item["plugin_id"]))

    def list_plugins(self) -> List[Dict[str, Any]]:
        if not self._plugins:
            self.register_builtins()
        items = self.list_all()
        if not any(item["plugin_id"] == "sweetiebot.local_dialogue_provider" for item in items):
            items.append({"plugin_id": "sweetiebot.local_dialogue_provider", "plugin_type": "dialogue_provider", "priority": 10})
        return items

    def health_summary(self) -> Dict[str, Any]:
        return summarize_plugin_health(self.plugins())

    def get_best_plugin(self, plugin_type: str | PluginType) -> Optional[BasePlugin]:
        items = self.get_by_type(plugin_type)
        return items[0] if items else None

    def get_memory_store(self) -> Optional[BasePlugin]:
        return self.get_best_plugin(PluginType.MEMORY_STORE)

    def get_telemetry_sink(self) -> Optional[BasePlugin]:
        return self.get_best_plugin(PluginType.TELEMETRY_SINK)

    def get_attention_strategy(self) -> Optional[BasePlugin]:
        return self.get_best_plugin(PluginType.ATTENTION_STRATEGY)

    def get_perception_sources(self) -> List[BasePlugin]:
        return self.get_by_type(PluginType.PERCEPTION_SOURCE)

    def get_dialogue_provider(self) -> Optional[BasePlugin]:
        return self.get_best_plugin(PluginType.DIALOGUE_PROVIDER)

    def configure_from_mapping(self, payload: Dict[str, Any]) -> List[str]:
        plugins = payload.get("plugins", payload)
        configured: List[str] = []
        for plugin_id, config in plugins.items():
            plugin = self.get(plugin_id)
            if plugin is None:
                continue
            plugin.configure(dict(config or {}))
            configured.append(plugin_id)
        return configured

    def configure_from_yaml(self, path: str) -> List[str]:
        return self.configure_from_mapping(load_plugin_config(path))

    def run_dialogue(self, *, user_text: str, runtime_context: Dict[str, Any]) -> Dict[str, Any]:
        plugin = self.get_dialogue_provider()
        if plugin is None:
            raise PluginError("No dialogue provider registered")
        result = plugin.generate_reply(user_text=user_text, runtime_context=runtime_context)
        if hasattr(result, "to_dict"):
            return result.to_dict()
        return dict(result)

    def apply_safety_policy(self, *, reply: DialogueReply, runtime_context: Dict[str, Any]) -> DialogueReply:
        policies = self.get_by_type(PluginType.SAFETY_POLICY)
        result = reply
        for plugin in policies:
            result = plugin.apply(result, context=runtime_context)
        return result

    def iter_routine_payloads(self) -> Dict[str, Dict[str, Any]]:
        payloads: Dict[str, Dict[str, Any]] = {}
        for plugin in self.get_by_type(PluginType.ROUTINE_PACK):
            for routine in plugin.get_routines():
                payloads[routine["routine_id"]] = dict(routine)
        return payloads

    def plugin_summary(self) -> Dict[str, object]:
        return {
            "count": len(self._plugins),
            "plugin_ids": sorted(self._plugins.keys()),
            "types": sorted({str(self._manifest_attr(p, 'plugin_type').value if hasattr(self._manifest_attr(p, 'plugin_type'), 'value') else self._manifest_attr(p, 'plugin_type')) for p in self._plugins.values()}),
        }

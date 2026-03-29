from __future__ import annotations

from collections import defaultdict
from importlib.metadata import entry_points
from typing import Any

from sweetiebot.dialogue.contracts import DialogueReply
from sweetiebot.plugins.base import (
    BasePlugin,
    DialogueProviderPlugin,
    PluginError,
    RoutinePackPlugin,
    SafetyPolicyPlugin,
)
from sweetiebot.plugins.builtins import (
    DefaultSafetyPolicyPlugin,
    DemoRoutinePackPlugin,
    LocalDialogueProviderPlugin,
)
from sweetiebot.plugins.config import load_plugin_config
from sweetiebot.plugins.manifest import PluginManifest
from sweetiebot.plugins.types import PluginType

ENTRY_POINT_GROUP = "sweetiebot.plugins"


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}
        self._by_type: dict[PluginType, list[str]] = defaultdict(list)

    def register(self, plugin: BasePlugin) -> PluginManifest:
        plugin.validate()
        plugin_id = plugin.plugin_id
        if plugin_id in self._plugins:
            raise PluginError(f"Plugin already registered: {plugin_id}")
        self._plugins[plugin_id] = plugin
        self._by_type[plugin.plugin_type].append(plugin_id)
        self._by_type[plugin.plugin_type].sort(
            key=lambda pid: self._plugins[pid].manifest().priority
        )
        return plugin.manifest()

    def register_builtins(self) -> None:
        if "sweetiebot.default_safety_policy" not in self._plugins:
            self.register(DefaultSafetyPolicyPlugin())
        if "sweetiebot.local_dialogue" not in self._plugins:
            self.register(LocalDialogueProviderPlugin())
        if "sweetiebot.demo_routines" not in self._plugins:
            self.register(DemoRoutinePackPlugin())

    def discover_entry_points(self) -> list[str]:
        loaded: list[str] = []
        for ep in entry_points(group=ENTRY_POINT_GROUP):
            plugin_cls = ep.load()
            plugin = plugin_cls() if callable(plugin_cls) else plugin_cls
            self.register(plugin)
            loaded.append(ep.name)
        return loaded

    def configure_from_mapping(self, config: dict[str, dict[str, Any]]) -> list[str]:
        configured: list[str] = []
        for plugin_id, plugin_config in config.items():
            plugin = self._plugins.get(plugin_id)
            if plugin is None:
                raise PluginError(f"Unknown plugin in config: {plugin_id}")
            plugin.configure(plugin_config)
            configured.append(plugin_id)
        return configured

    def configure_from_yaml(self, path: str) -> list[str]:
        return self.configure_from_mapping(load_plugin_config(path))

    def get(self, plugin_id: str) -> BasePlugin:
        return self._plugins[plugin_id]

    def list_all(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for plugin_id in sorted(self._plugins):
            plugin = self._plugins[plugin_id]
            payload = plugin.manifest().to_dict()
            payload["health"] = plugin.healthcheck().to_dict()
            results.append(payload)
        return results

    def list_ids_for_type(self, plugin_type: PluginType) -> list[str]:
        return list(self._by_type.get(plugin_type, []))

    def get_primary(self, plugin_type: PluginType) -> BasePlugin | None:
        ids = self.list_ids_for_type(plugin_type)
        if not ids:
            return None
        return self._plugins[ids[0]]

    def run_dialogue(self, *, user_text: str, runtime_context: dict[str, Any]) -> dict[str, Any]:
        plugin = self.get_primary(PluginType.DIALOGUE_PROVIDER)
        if plugin is None:
            raise PluginError("No dialogue provider plugin is registered")
        if not isinstance(plugin, DialogueProviderPlugin):
            raise PluginError("Primary dialogue plugin does not implement DialogueProviderPlugin")
        return plugin.generate_reply(user_text=user_text, runtime_context=runtime_context)

    def apply_safety_policy(
        self,
        *,
        reply: DialogueReply,
        runtime_context: dict[str, Any],
    ) -> DialogueReply:
        current = reply
        for plugin_id in self.list_ids_for_type(PluginType.SAFETY_POLICY):
            plugin = self._plugins[plugin_id]
            if not isinstance(plugin, SafetyPolicyPlugin):
                continue
            current = plugin.filter_reply(reply=current, runtime_context=runtime_context)
        return current

    def iter_routine_payloads(self) -> dict[str, dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for plugin_id in self.list_ids_for_type(PluginType.ROUTINE_PACK):
            plugin = self._plugins[plugin_id]
            if not isinstance(plugin, RoutinePackPlugin):
                continue
            merged.update(plugin.list_routines())
        return merged

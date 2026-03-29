from __future__ import annotations

from collections import defaultdict
from importlib.metadata import entry_points
from typing import Any

import yaml

from sweetiebot.dialogue.models import DialogueReply
from sweetiebot.errors import ConfigurationError, PluginError
from sweetiebot.observability import EventLogger
from sweetiebot.plugins.base import DialogueProviderPlugin, PluginBase, RoutinePackPlugin, SafetyPolicyPlugin
from sweetiebot.plugins.builtins import (
    DefaultSafetyPolicyPlugin,
    DemoRoutinePackPlugin,
    LocalDialogueProviderPlugin,
)
from sweetiebot.plugins.types import PluginType

_logger = EventLogger(__name__)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[PluginType, list[PluginBase]] = defaultdict(list)
        self.register(LocalDialogueProviderPlugin())
        self.register(DemoRoutinePackPlugin())
        self.register(DefaultSafetyPolicyPlugin())

    def register(self, plugin: PluginBase) -> None:
        manifest = plugin.manifest()
        self._plugins[manifest.plugin_type].append(plugin)
        self._plugins[manifest.plugin_type].sort(key=lambda p: p.manifest().priority)
        _logger.plugin_loaded(manifest.plugin_id, manifest.plugin_type, built_in=manifest.built_in)

    def discover_entry_points(self) -> int:
        count = 0
        eps = entry_points()
        group = eps.select(group="sweetiebot.plugins") if hasattr(eps, "select") else eps.get("sweetiebot.plugins", [])
        for ep in group:
            plugin_cls = ep.load()
            plugin = plugin_cls()
            self.register(plugin)
            count += 1
        return count

    def configure_from_mapping(self, config: dict[str, Any]) -> None:
        plugins_cfg = config.get("plugins", {})
        if not isinstance(plugins_cfg, dict):
            raise ConfigurationError("Plugin configuration must include a 'plugins' mapping.")
        for family_plugins in self._plugins.values():
            for plugin in family_plugins:
                plugin.configure(plugins_cfg.get(plugin.manifest().plugin_id, {}))

    def configure_from_yaml(self, yaml_text: str) -> None:
        try:
            data = yaml.safe_load(yaml_text) or {}
        except Exception as exc:
            raise ConfigurationError(f"Invalid plugin YAML config: {exc}") from exc
        self.configure_from_mapping(data)

    def list_plugins(self) -> list[dict[str, Any]]:
        out = []
        for family_plugins in self._plugins.values():
            for plugin in family_plugins:
                manifest = plugin.manifest()
                out.append(manifest.model_dump())
        return sorted(out, key=lambda item: (item["plugin_type"], item["priority"], item["plugin_id"]))

    def get_primary_dialogue_provider(self) -> DialogueProviderPlugin:
        providers = self._plugins[PluginType.DIALOGUE_PROVIDER]
        if not providers:
            raise PluginError("No dialogue provider plugins registered.")
        return providers[0]  # type: ignore[return-value]

    def get_all_routines(self) -> list[dict[str, Any]]:
        routines = []
        for plugin in self._plugins[PluginType.ROUTINE_PACK]:
            assert isinstance(plugin, RoutinePackPlugin)
            routines.extend(plugin.get_routines())
        return routines

    def apply_safety_policy(self, reply: DialogueReply, context: dict[str, Any] | None = None) -> DialogueReply:
        result = reply
        for plugin in self._plugins[PluginType.SAFETY_POLICY]:
            assert isinstance(plugin, SafetyPolicyPlugin)
            result = plugin.apply(result, context=context)
        return result

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sweetiebot.plugins.base import PluginError


class PluginConfigError(PluginError):
    pass


def load_plugin_config(path: str | Path) -> dict[str, dict[str, Any]]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise PluginConfigError("Plugin config root must be a mapping")
    plugins = payload.get("plugins", payload)
    if not isinstance(plugins, dict):
        raise PluginConfigError("Plugin config must contain a 'plugins' mapping")
    normalized: dict[str, dict[str, Any]] = {}
    for plugin_id, config in plugins.items():
        if not isinstance(plugin_id, str) or not plugin_id.strip():
            raise PluginConfigError("Each plugin config entry needs a non-empty plugin id")
        if config is None:
            normalized[plugin_id] = {}
        elif isinstance(config, dict):
            normalized[plugin_id] = dict(config)
        else:
            raise PluginConfigError(f"Plugin config for {plugin_id!r} must be a mapping")
    return normalized

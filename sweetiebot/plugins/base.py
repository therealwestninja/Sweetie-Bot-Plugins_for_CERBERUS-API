from __future__ import annotations

from typing import Any

from sweetiebot.dialogue.contracts import DialogueReply
from sweetiebot.plugins.manifest import PluginHealth, PluginManifest


class PluginError(RuntimeError):
    pass


class BasePlugin:
    def __init__(self, manifest: PluginManifest) -> None:
        self._manifest = manifest
        self._config: dict[str, Any] = {}

    @property
    def plugin_id(self) -> str:
        return self._manifest.plugin_id

    @property
    def plugin_type(self):
        return self._manifest.plugin_type

    def manifest(self) -> PluginManifest:
        return self._manifest

    def configure(self, config: dict[str, Any] | None = None) -> None:
        self._config = dict(config or {})

    def validate(self) -> None:
        if not self._manifest.plugin_id:
            raise PluginError("plugin_id is required")

    def healthcheck(self) -> PluginHealth:
        return PluginHealth(ok=True, status="ok")

    def shutdown(self) -> None:
        return None


class DialogueProviderPlugin(BasePlugin):
    def generate_reply(self, *, user_text: str, runtime_context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class RoutinePackPlugin(BasePlugin):
    def list_routines(self) -> dict[str, dict[str, Any]]:
        raise NotImplementedError


class SafetyPolicyPlugin(BasePlugin):
    def filter_reply(
        self,
        *,
        reply: DialogueReply,
        runtime_context: dict[str, Any],
    ) -> DialogueReply:
        raise NotImplementedError

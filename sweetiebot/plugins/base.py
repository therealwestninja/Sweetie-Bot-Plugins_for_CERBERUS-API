from __future__ import annotations

from typing import Any

from sweetiebot.dialogue.models import DialogueReply
from sweetiebot.plugins.manifest import PluginManifest
from sweetiebot.plugins.types import PluginType


class PluginBase:
    def manifest(self) -> PluginManifest:
        raise NotImplementedError

    def configure(self, config: dict[str, Any] | None = None) -> None:
        self._config = dict(config or {})

    def healthcheck(self) -> dict[str, Any]:
        return {"ok": True}


class DialogueProviderPlugin(PluginBase):
    plugin_type = PluginType.DIALOGUE_PROVIDER

    def generate_reply(self, text: str, context: dict[str, Any] | None = None) -> DialogueReply:
        raise NotImplementedError


class RoutinePackPlugin(PluginBase):
    plugin_type = PluginType.ROUTINE_PACK

    def get_routines(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class SafetyPolicyPlugin(PluginBase):
    plugin_type = PluginType.SAFETY_POLICY

    def apply(self, reply: DialogueReply, context: dict[str, Any] | None = None) -> DialogueReply:
        return reply

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from sweetiebot.dialogue.models import DialogueReply
from sweetiebot.observability import EventLogger
from sweetiebot.plugins.registry import PluginRegistry

_logger = EventLogger(__name__)


@dataclass
class RuntimeState:
    persona_id: str = "sweetiebot.core"
    current_emote_id: str = "calm_neutral"
    current_routine_id: str | None = None
    current_accessory_scene_id: str | None = None
    safe_mode: bool = False
    degraded_mode: bool = False
    last_input: str | None = None
    last_reply: dict[str, Any] | None = None
    routines: dict[str, dict[str, Any]] = field(default_factory=dict)


class SweetieBotRuntime:
    def __init__(self, plugin_registry: PluginRegistry | None = None) -> None:
        self.plugins = plugin_registry or PluginRegistry()
        self.state = RuntimeState()
        for routine in self.plugins.get_all_routines():
            self.state.routines[routine["routine_id"]] = routine

    def plugin_summary(self) -> list[dict[str, Any]]:
        return self.plugins.list_plugins()

    def say(self, text: str, context: dict[str, Any] | None = None) -> DialogueReply:
        self.state.last_input = text
        provider = self.plugins.get_primary_dialogue_provider()
        reply = provider.generate_reply(text, context=context or {})
        reply = self.plugins.apply_safety_policy(reply, context=context or {})

        if reply.routine_id and reply.routine_id not in self.state.routines:
            self.state.degraded_mode = True
            reply.routine_id = None
            reply.fallback = True

        old_emote = self.state.current_emote_id
        self.state.current_emote_id = reply.emote_id or self.state.current_emote_id
        self.state.current_routine_id = reply.routine_id
        self.state.last_reply = reply.model_dump()

        if old_emote != self.state.current_emote_id:
            _logger.runtime_state_changed("current_emote_id", old_emote, self.state.current_emote_id)
        _logger.dialogue_generated(intent=reply.intent, emote_id=reply.emote_id, routine_id=reply.routine_id)
        return reply

    def snapshot(self) -> dict[str, Any]:
        return asdict(self.state)

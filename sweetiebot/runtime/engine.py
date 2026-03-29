from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sweetiebot.dialogue.contracts import DialogueReply
from sweetiebot.dialogue.manager import DialogueManager
from sweetiebot.persona.loader import load_persona
from sweetiebot.plugins import PluginRegistry
from sweetiebot.routines.registry import RoutineRegistry


@dataclass(slots=True)
class RuntimeState:
    persona_id: str
    current_emote_id: str | None = None
    current_routine_id: str | None = None
    current_accessory_scene_id: str | None = None
    safe_mode: bool = False
    degraded_mode: bool = False
    last_user_text: str | None = None
    last_reply_text: str | None = None
    last_intent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SweetieBotRuntime:
    """High-level orchestration for persona, dialogue, routines, and plugin-driven extension.

    The runtime stays bounded by design. Plugins are allowed to suggest structured behavior,
    but transport, actuation, and CERBERUS safety remain downstream concerns.
    """

    def __init__(
        self,
        *,
        dialogue: DialogueManager | None = None,
        routines: RoutineRegistry | None = None,
        plugins: PluginRegistry | None = None,
    ) -> None:
        self.dialogue = dialogue or DialogueManager()
        self.routines = routines or RoutineRegistry()
        self.plugins = plugins or PluginRegistry()
        self._persona_payload: dict[str, Any] | None = None
        self.plugins.register_builtins()
        self._bootstrap_routines_from_plugins()
        self.state = RuntimeState(
            persona_id=self.dialogue.persona_id,
            current_emote_id=self.dialogue.rules.default_emote,
            current_accessory_scene_id=self.dialogue.rules.default_accessory_scene,
        )

    def _bootstrap_routines_from_plugins(self) -> None:
        for routine_id, payload in self.plugins.iter_routine_payloads().items():
            if routine_id not in self.routines.list_ids():
                self.routines.register(routine_id, payload)

    def plugin_summary(self) -> list[dict[str, Any]]:
        return self.plugins.list_all()

    def configure_plugins(self, payload: dict[str, dict[str, Any]]) -> list[str]:
        configured = self.plugins.configure_from_mapping(payload)
        return configured

    def configure_plugins_from_file(self, path: str) -> list[str]:
        return self.plugins.configure_from_yaml(path)

    def configure_persona(self, payload: dict[str, Any]) -> RuntimeState:
        self._persona_payload = dict(payload)
        self.dialogue.configure_persona(payload)
        self.state.persona_id = self.dialogue.persona_id
        self.state.current_emote_id = self.dialogue.rules.default_emote
        self.state.current_accessory_scene_id = self.dialogue.rules.default_accessory_scene
        if not self.state.current_routine_id:
            self.state.current_routine_id = self.dialogue.rules.default_routine
        return self.state

    def load_persona_file(self, path: str) -> RuntimeState:
        payload = load_persona(path)
        return self.configure_persona(payload)

    def register_routine(self, routine_id: str, payload: dict[str, Any]) -> None:
        self.routines.register(routine_id, payload)

    def apply_operator_stop(self) -> RuntimeState:
        self.state.current_routine_id = "return_to_neutral"
        self.state.current_emote_id = "calm_neutral"
        self.state.safe_mode = True
        return self.state

    def reset_neutral(self) -> RuntimeState:
        self.state.current_routine_id = "return_to_neutral"
        self.state.current_emote_id = self.dialogue.rules.default_emote
        self.state.current_accessory_scene_id = self.dialogue.rules.default_accessory_scene
        self.state.safe_mode = False
        return self.state

    def _reply_from_plugins(self, user_text: str) -> DialogueReply:
        runtime_context = {
            "persona_payload": self._persona_payload,
            "runtime_state": self.state.to_dict(),
        }
        payload = self.plugins.run_dialogue(user_text=user_text, runtime_context=runtime_context)
        reply = DialogueReply.from_dict(payload).normalized()
        return self.plugins.apply_safety_policy(reply=reply, runtime_context=runtime_context)

    def handle_text(self, user_text: str) -> dict[str, Any]:
        reply = self._reply_from_plugins(user_text)
        directive = reply.directive

        routine_id = directive.routine_id
        if routine_id and routine_id not in self.routines.list_ids():
            directive.routine_id = None
            self.state.degraded_mode = True
        else:
            self.state.degraded_mode = False

        self.state.last_user_text = user_text
        self.state.last_reply_text = reply.text
        self.state.last_intent = reply.intent.value
        self.state.current_emote_id = directive.emote_id or self.state.current_emote_id
        self.state.current_accessory_scene_id = (
            directive.accessory_scene_id or self.state.current_accessory_scene_id
        )
        self.state.current_routine_id = directive.routine_id or self.state.current_routine_id
        self.state.persona_id = self.dialogue.persona_id
        self.state.safe_mode = reply.intent.value == "cancel"

        return {
            "reply": reply.to_dict(),
            "state": self.state.to_dict(),
        }

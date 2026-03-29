from __future__ import annotations

from typing import Any

from sweetiebot.dialogue.manager import DialogueManager
from sweetiebot.plugins.base import DialogueProviderPlugin, RoutinePackPlugin
from sweetiebot.plugins.manifest import PluginManifest
from sweetiebot.plugins.types import PluginType


class LocalDialogueProviderPlugin(DialogueProviderPlugin):
    def __init__(self, manager: DialogueManager | None = None) -> None:
        super().__init__(
            PluginManifest(
                plugin_id="sweetiebot.local_dialogue",
                plugin_type=PluginType.DIALOGUE_PROVIDER,
                version="0.1.0",
                display_name="Local Dialogue Provider",
                description="Rule-based local dialogue provider with bounded Sweetie Bot output.",
                capabilities=["local", "bounded_output", "fallback_safe"],
                priority=10,
                supports_degraded_mode=True,
            )
        )
        self.manager = manager or DialogueManager()

    def generate_reply(self, *, user_text: str, runtime_context: dict[str, Any]) -> dict[str, Any]:
        persona_payload = runtime_context.get("persona_payload")
        if persona_payload:
            self.manager.configure_persona(persona_payload)
        return self.manager.reply_for(user_text).to_dict()


class DemoRoutinePackPlugin(RoutinePackPlugin):
    def __init__(self) -> None:
        super().__init__(
            PluginManifest(
                plugin_id="sweetiebot.demo_routines",
                plugin_type=PluginType.ROUTINE_PACK,
                version="0.1.0",
                display_name="Demo Routine Pack",
                description="Reusable safe demo routines for staged Sweetie Bot behavior.",
                capabilities=["greet_guest", "photo_pose", "idle_cute", "return_to_neutral"],
                priority=20,
                supports_degraded_mode=True,
            )
        )

    def list_routines(self) -> dict[str, dict[str, Any]]:
        return {
            "greet_guest": {
                "summary": "Friendly first-contact greeting.",
                "interruptible": True,
                "steps": [{"speak": "Hi there!"}, {"emote": "happy_pose"}],
            },
            "photo_pose": {
                "summary": "Short pose for a camera moment.",
                "interruptible": True,
                "steps": [{"emote": "happy_pose"}, {"pause_ms": 1000}],
            },
            "idle_cute": {
                "summary": "Cute waiting loop stub.",
                "interruptible": True,
                "steps": [{"emote": "curious_headtilt"}, {"pause_ms": 800}],
            },
            "return_to_neutral": {
                "summary": "Safe neutral fallback routine.",
                "interruptible": True,
                "steps": [{"emote": "calm_neutral"}, {"pause_ms": 600}],
            },
        }

from __future__ import annotations

from typing import Any

from sweetiebot.dialogue.contracts import DialogueReply
from sweetiebot.dialogue.manager import DialogueManager
from sweetiebot.plugins.base import DialogueProviderPlugin, RoutinePackPlugin, SafetyPolicyPlugin
from sweetiebot.plugins.manifest import PluginHealth, PluginManifest
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


class DefaultSafetyPolicyPlugin(SafetyPolicyPlugin):
    def __init__(self) -> None:
        super().__init__(
            PluginManifest(
                plugin_id="sweetiebot.default_safety_policy",
                plugin_type=PluginType.SAFETY_POLICY,
                version="0.1.0",
                display_name="Default Safety Policy",
                description="Filters plugin output into a runtime-safe reply contract.",
                capabilities=["clip_text", "block_unsupported_routines", "neutral_on_cancel"],
                priority=5,
                supports_degraded_mode=True,
                config_schema={
                    "max_spoken_chars": {"type": "integer", "default": 240},
                    "blocked_terms": {"type": "array", "default": []},
                },
            )
        )
        self._max_spoken_chars = 240
        self._blocked_terms: list[str] = []

    def configure(self, config: dict[str, Any] | None = None) -> None:
        super().configure(config)
        self._max_spoken_chars = int(self._config.get("max_spoken_chars", 240))
        blocked = self._config.get("blocked_terms", [])
        self._blocked_terms = [str(term).lower() for term in blocked if str(term).strip()]

    def healthcheck(self) -> PluginHealth:
        return PluginHealth(
            ok=True,
            status="ok",
            details={
                "max_spoken_chars": self._max_spoken_chars,
                "blocked_terms": list(self._blocked_terms),
            },
        )

    def filter_reply(
        self,
        *,
        reply: DialogueReply,
        runtime_context: dict[str, Any],
    ) -> DialogueReply:
        normalized = reply.normalized()
        text_lower = normalized.text.lower()
        if any(term in text_lower for term in self._blocked_terms):
            return DialogueReply.from_dict(
                {
                    "intent": "cancel",
                    "text": "I should switch back to a safe neutral response.",
                    "confidence": 1.0,
                    "fallback_mode": True,
                    "directive": {
                        "emote_id": "calm_neutral",
                        "routine_id": "return_to_neutral",
                        "operator_note": "Blocked by safety policy.",
                    },
                }
            ).normalized()

        if len(normalized.text) > self._max_spoken_chars:
            normalized.text = normalized.text[: self._max_spoken_chars].rstrip() + "…"
            normalized.fallback_mode = True
            note = normalized.directive.operator_note or ""
            normalized.directive.operator_note = (note + " Clipped by safety policy.").strip()
        return normalized

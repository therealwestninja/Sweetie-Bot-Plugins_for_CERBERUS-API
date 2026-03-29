from __future__ import annotations

from sweetiebot.dialogue.models import DialogueReply
from sweetiebot.plugins.base import DialogueProviderPlugin, RoutinePackPlugin, SafetyPolicyPlugin
from sweetiebot.plugins.manifest import PluginManifest
from sweetiebot.plugins.types import PluginType


class LocalDialogueProviderPlugin(DialogueProviderPlugin):
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="sweetiebot.local_dialogue_provider",
            display_name="Local Dialogue Provider",
            plugin_type=PluginType.DIALOGUE_PROVIDER,
            built_in=True,
            priority=10,
            description="Simple local bounded dialogue provider.",
        )

    def generate_reply(self, text: str, context: dict | None = None) -> DialogueReply:
        lowered = text.strip().lower()
        if any(word in lowered for word in ("hello", "hi", "hey")):
            return DialogueReply(
                intent="greet",
                spoken_text="Hi there! I'm Sweetie Bot!",
                emote_id="happy_ears_up",
                routine_id="greet_guest",
                confidence=0.92,
            )
        return DialogueReply(
            intent="chat",
            spoken_text=f"I heard: {text[:80]}",
            emote_id="calm_neutral",
            confidence=0.65,
        )


class DemoRoutinePackPlugin(RoutinePackPlugin):
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="sweetiebot.demo_routine_pack",
            display_name="Demo Routine Pack",
            plugin_type=PluginType.ROUTINE_PACK,
            built_in=True,
            priority=10,
            description="Small built-in demo routine pack.",
        )

    def get_routines(self) -> list[dict]:
        return [
            {
                "routine_id": "greet_guest",
                "summary": "Friendly greeting routine.",
                "interruptible": True,
                "steps": [
                    {"action": "speak", "value": "Hi there!"},
                    {"action": "emote", "value": "happy_ears_up"},
                ],
            },
            {
                "routine_id": "return_to_neutral",
                "summary": "Reset to neutral state.",
                "interruptible": True,
                "steps": [
                    {"action": "emote", "value": "calm_neutral"},
                ],
            },
        ]


class DefaultSafetyPolicyPlugin(SafetyPolicyPlugin):
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="sweetiebot.default_safety_policy",
            display_name="Default Safety Policy",
            plugin_type=PluginType.SAFETY_POLICY,
            built_in=True,
            priority=10,
            description="Simple response clipping and blocked term policy.",
        )

    def apply(self, reply: DialogueReply, context: dict | None = None) -> DialogueReply:
        config = getattr(self, "_config", {})
        blocked_terms = [str(item).lower() for item in config.get("blocked_terms", [])]
        max_spoken_chars = int(config.get("max_spoken_chars", 120))

        text_lower = reply.spoken_text.lower()
        if any(term in text_lower for term in blocked_terms):
            reply.spoken_text = "Let's keep things safe and friendly."
            reply.intent = "cancel"
            reply.emote_id = "calm_neutral"
            reply.routine_id = "return_to_neutral"
            reply.fallback = True

        if len(reply.spoken_text) > max_spoken_chars:
            reply.spoken_text = reply.spoken_text[: max_spoken_chars - 1].rstrip() + "…"
            reply.fallback = True

        return reply

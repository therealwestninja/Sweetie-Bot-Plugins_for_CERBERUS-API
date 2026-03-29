from __future__ import annotations

from sweetiebot.character.intent_types import IntentType
from sweetiebot.dialogue.contracts import DialogueDirective, DialogueReply
from sweetiebot.plugins.base import DialogueProviderPlugin, RoutinePackPlugin, SafetyPolicyPlugin
from sweetiebot.plugins.manifest import PluginManifest
from sweetiebot.plugins.types import PluginType


class LocalDialogueProviderPlugin(DialogueProviderPlugin):
    plugin_id = "sweetiebot.local_dialogue"
    priority = 10

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self.plugin_id,
            display_name="Local Dialogue Provider",
            plugin_type=PluginType.DIALOGUE_PROVIDER,
            built_in=True,
            priority=self.priority,
            description="Simple local bounded dialogue provider.",
        )

    def generate_reply(self, user_text: str, runtime_context: dict | None = None, **_: object) -> dict:
        lowered = (user_text or "").strip().lower()
        persona = ((runtime_context or {}).get("persona_payload") or {})
        preferred_greeting = persona.get("preferred_greeting")
        if any(word in lowered for word in ("hello", "hi", "hey")):
            text = preferred_greeting or "Hi there! I'm Sweetie Bot!"
            directive = DialogueDirective(emote_id="curious_headtilt", routine_id="greet_guest")
            return DialogueReply(intent=IntentType.GREET, text=text, directive=directive, confidence=0.92).to_dict()
        if any(word in lowered for word in ("photo", "camera", "pose")):
            directive = DialogueDirective(emote_id="happy_pose", routine_id="photo_pose")
            return DialogueReply(intent=IntentType.ROUTINE, text="Okay! I'll hold a cute pose.", directive=directive, confidence=0.88).to_dict()
        if any(word in lowered for word in ("stop", "cancel", "quiet")):
            directive = DialogueDirective(emote_id="calm_neutral", routine_id="return_to_neutral")
            return DialogueReply(intent=IntentType.CANCEL, text="Okay. I am stopping and returning to neutral.", directive=directive, confidence=0.95).to_dict()
        directive = DialogueDirective(emote_id="curious_headtilt", routine_id=None)
        return DialogueReply(intent=IntentType.SPEAK, text=f"I heard: {user_text[:80]}", directive=directive, confidence=0.65).to_dict()


class DemoRoutinePackPlugin(RoutinePackPlugin):
    plugin_id = "sweetiebot.demo_routines"
    priority = 10

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self.plugin_id,
            display_name="Demo Routine Pack",
            plugin_type=PluginType.ROUTINE_PACK,
            built_in=True,
            priority=self.priority,
            description="Small built-in demo routine pack.",
        )

    def get_routines(self) -> list[dict]:
        return [
            {
                "routine_id": "greet_guest",
                "summary": "Friendly greeting routine.",
                "interruptible": True,
                "steps": [
                    {"type": "speak", "value": "Hi there!", "duration_ms": 1800},
                    {"type": "emote", "value": "warm_smile", "duration_ms": 600},
                    {"type": "pause", "value": 400, "duration_ms": 400},
                ],
            },
            {
                "routine_id": "photo_pose",
                "summary": "Cute photo pose.",
                "interruptible": True,
                "steps": [
                    {"type": "focus", "value": "camera", "duration_ms": 300},
                    {"type": "emote", "value": "happy_pose", "duration_ms": 1200},
                    {"type": "pause", "value": 1200, "duration_ms": 1200},
                ],
            },
            {
                "routine_id": "idle_cute",
                "summary": "Gentle idle animation.",
                "interruptible": True,
                "steps": [{"type": "emote", "value": "curious_headtilt", "duration_ms": 900}],
            },
            {
                "routine_id": "return_to_neutral",
                "summary": "Reset to neutral state.",
                "interruptible": True,
                "steps": [{"type": "emote", "value": "calm_neutral", "duration_ms": 600}],
            },
        ]


class DefaultSafetyPolicyPlugin(SafetyPolicyPlugin):
    plugin_id = "sweetiebot.default_safety_policy"
    priority = 10

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self.plugin_id,
            display_name="Default Safety Policy",
            plugin_type=PluginType.SAFETY_POLICY,
            built_in=True,
            priority=self.priority,
            description="Simple response clipping and blocked term policy.",
        )

    def apply(self, reply: DialogueReply, context: dict | None = None) -> DialogueReply:
        del context
        blocked_terms = [str(item).lower() for item in self.config.get("blocked_terms", [])]
        max_spoken_chars = int(self.config.get("max_spoken_chars", 120))
        text_lower = reply.text.lower()
        if any(term in text_lower for term in blocked_terms):
            reply.text = "Let's keep things safe and friendly."
            reply.intent = IntentType.CANCEL
            reply.directive.emote_id = "calm_neutral"
            reply.directive.routine_id = "return_to_neutral"
            reply.fallback_mode = True
        if len(reply.text) > max_spoken_chars:
            reply.text = reply.text[: max_spoken_chars - 1].rstrip() + "…"
            reply.fallback_mode = True
        return reply

    def healthcheck(self) -> dict:
        return {"healthy": True, "plugin_id": self.plugin_id, "max_spoken_chars": int(self.config.get("max_spoken_chars", 120)), "blocked_terms": list(self.config.get("blocked_terms", []))}

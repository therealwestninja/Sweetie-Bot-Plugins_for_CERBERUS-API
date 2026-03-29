from __future__ import annotations

from typing import Dict, Optional

from sweetiebot.dialogue.models import DialogueResponse
from sweetiebot.plugins.base import DialogueProviderPlugin


class RuleBasedDialogueProviderPlugin(DialogueProviderPlugin):
    plugin_id = "sweetiebot.dialogue.rule_based"

    def __init__(self) -> None:
        self.config = {}

    def manifest(self) -> Dict[str, object]:
        base = super().manifest()
        base["capabilities"] = ["generate_reply"]
        return base

    def generate_reply(
        self,
        *,
        user_text: Optional[str],
        current_mood: str,
        current_focus: Optional[str],
        active_routine: Optional[str],
        safe_mode: bool = False,
        degraded_mode: bool = False,
    ) -> DialogueResponse:
        text = (user_text or "").lower().strip()

        if degraded_mode:
            return DialogueResponse(
                spoken_text="I'm in a limited mode right now.",
                intent="reply",
                emote_id="calm_neutral",
                routine_id=None,
                confidence=0.95,
                source=self.plugin_id,
                metadata={"reason": "degraded_mode"},
            )

        if safe_mode:
            return DialogueResponse(
                spoken_text="I'm staying calm and neutral right now.",
                intent="reply",
                emote_id="calm_neutral",
                routine_id="return_to_neutral",
                confidence=0.95,
                source=self.plugin_id,
                metadata={"reason": "safe_mode"},
            )

        if any(token in text for token in ["hello", "hi", "hey"]):
            return DialogueResponse(
                spoken_text="Hi there!",
                intent="greet",
                emote_id="warm_smile",
                routine_id="greet_guest",
                confidence=0.9,
                source=self.plugin_id,
            )

        if any(token in text for token in ["photo", "picture", "pose"]):
            return DialogueResponse(
                spoken_text="Okay! I'll hold a cute pose.",
                intent="pose",
                emote_id="happy_pose",
                routine_id="photo_pose",
                confidence=0.88,
                source=self.plugin_id,
            )

        if any(token in text for token in ["stop", "cancel", "pause", "quiet"]):
            return DialogueResponse(
                spoken_text="Okay, stopping now.",
                intent="cancel",
                emote_id="calm_neutral",
                routine_id="return_to_neutral",
                confidence=0.92,
                source=self.plugin_id,
            )

        if "?" in text:
            emote = "curious_tilt" if current_mood == "curious" else "warm_smile"
            return DialogueResponse(
                spoken_text="Let me think about that.",
                intent="question_reply",
                emote_id=emote,
                routine_id=None,
                confidence=0.78,
                source=self.plugin_id,
            )

        if current_mood in {"happy", "excited"} and not active_routine:
            return DialogueResponse(
                spoken_text="I'm feeling pretty cheerful right now.",
                intent="mood_reply",
                emote_id="happy_bounce",
                routine_id="idle_cute",
                confidence=0.72,
                source=self.plugin_id,
            )

        return DialogueResponse(
            spoken_text="I'm here and listening.",
            intent="reply",
            emote_id="calm_neutral",
            routine_id=None,
            confidence=0.7,
            source=self.plugin_id,
            metadata={"fallback": True, "focus": current_focus},
        )

    def healthcheck(self) -> Dict[str, object]:
        return {
            "healthy": True,
            "plugin_id": self.plugin_id,
            "mode": "rule_based_local",
        }

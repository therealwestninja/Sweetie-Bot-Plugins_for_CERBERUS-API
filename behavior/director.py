from __future__ import annotations

from typing import Any, Dict, Optional


class BehaviorDirector:
    def __init__(self) -> None:
        self.default_idle_routine = "idle_cute"

    def suggest(
        self,
        *,
        user_text: Optional[str],
        current_mood: str,
        focus_target: Optional[str],
        active_routine: Optional[str],
        safe_mode: bool = False,
        degraded_mode: bool = False,
    ) -> Dict[str, Any]:
        text = (user_text or "").lower().strip()

        if degraded_mode:
            return {
                "action": "speak_only",
                "priority": "high",
                "reason": "degraded_mode",
                "speak_text": "I'm in a limited mode right now.",
                "routine_id": None,
                "emote_id": "calm_neutral",
            }

        if safe_mode:
            return {
                "action": "return_to_neutral",
                "priority": "high",
                "reason": "safe_mode",
                "speak_text": "Returning to a calm neutral state.",
                "routine_id": "return_to_neutral",
                "emote_id": "calm_neutral",
            }

        if any(token in text for token in ["stop", "cancel", "quiet", "pause"]):
            return {
                "action": "cancel",
                "priority": "high",
                "reason": "user_stop_request",
                "speak_text": "Okay, stopping now.",
                "routine_id": "return_to_neutral",
                "emote_id": "calm_neutral",
            }

        if any(token in text for token in ["photo", "picture", "pose"]):
            return {
                "action": "routine",
                "priority": "medium",
                "reason": "photo_request",
                "speak_text": "Okay! I'll hold a cute pose.",
                "routine_id": "photo_pose",
                "emote_id": "happy_pose",
            }

        if any(token in text for token in ["hello", "hi", "hey"]):
            return {
                "action": "routine",
                "priority": "medium",
                "reason": "greeting",
                "speak_text": "Hi there!",
                "routine_id": "greet_guest",
                "emote_id": "warm_smile",
            }

        if "?" in text:
            emote = "curious_tilt" if current_mood == "curious" else "warm_smile"
            return {
                "action": "reply",
                "priority": "medium",
                "reason": "question",
                "speak_text": "Let me think about that.",
                "routine_id": None,
                "emote_id": emote,
            }

        if current_mood in {"excited", "happy"} and not active_routine:
            return {
                "action": "routine",
                "priority": "low",
                "reason": "positive_idle",
                "speak_text": None,
                "routine_id": self.default_idle_routine,
                "emote_id": "happy_bounce",
            }

        if current_mood == "sleepy":
            return {
                "action": "idle",
                "priority": "low",
                "reason": "sleepy_idle",
                "speak_text": None,
                "routine_id": None,
                "emote_id": "sleepy_blink",
            }

        return {
            "action": "reply",
            "priority": "low",
            "reason": "default",
            "speak_text": "I'm here and listening.",
            "routine_id": None,
            "emote_id": "calm_neutral",
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "default_idle_routine": self.default_idle_routine,
            "mode": "bounded_rule_based",
        }

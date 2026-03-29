from __future__ import annotations

from typing import Dict, Optional


class MoodEngine:
    VALID_MOODS = {
        "calm",
        "warm",
        "happy",
        "excited",
        "curious",
        "focused",
        "concerned",
        "startled",
        "sleepy",
    }

    EVENT_TO_MOOD = {
        "greet": "warm",
        "praise": "happy",
        "success": "happy",
        "play": "excited",
        "question": "curious",
        "task": "focused",
        "warning": "concerned",
        "loud_noise": "startled",
        "idle_long": "sleepy",
        "reset": "calm",
    }

    DECAY_ORDER = {
        "excited": "happy",
        "happy": "warm",
        "warm": "calm",
        "curious": "calm",
        "focused": "calm",
        "concerned": "calm",
        "startled": "concerned",
        "sleepy": "calm",
        "calm": "calm",
    }

    def __init__(self, default_mood: str = "calm") -> None:
        if default_mood not in self.VALID_MOODS:
            raise ValueError(f"Invalid default mood: {default_mood}")
        self.default_mood = default_mood

    def apply_event(self, current_mood: str, event: str) -> str:
        if current_mood not in self.VALID_MOODS:
            current_mood = self.default_mood
        if event not in self.EVENT_TO_MOOD:
            return current_mood
        return self.EVENT_TO_MOOD[event]

    def decay(self, current_mood: str) -> str:
        if current_mood not in self.VALID_MOODS:
            return self.default_mood
        return self.DECAY_ORDER.get(current_mood, self.default_mood)

    def infer_from_turn(
        self,
        user_text: str,
        reply_text: Optional[str] = None,
        current_mood: str = "calm",
    ) -> str:
        text = (user_text or "").lower()
        if any(token in text for token in ["hi", "hello", "hey"]):
            return "warm"
        if "?" in text:
            return "curious"
        if any(token in text for token in ["good job", "great", "awesome", "love"]):
            return "happy"
        if any(token in text for token in ["warning", "careful", "danger"]):
            return "concerned"
        if any(token in text for token in ["play", "dance", "sing"]):
            return "excited"
        return current_mood if current_mood in self.VALID_MOODS else self.default_mood

    def snapshot(self) -> Dict[str, object]:
        return {
            "default_mood": self.default_mood,
            "valid_moods": sorted(self.VALID_MOODS),
            "events": dict(self.EVENT_TO_MOOD),
        }

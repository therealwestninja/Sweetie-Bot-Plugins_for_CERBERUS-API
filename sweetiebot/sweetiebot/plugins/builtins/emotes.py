from __future__ import annotations

from typing import Dict, Optional

from sweetiebot.emotes.models import EmoteSelection
from sweetiebot.plugins.base import EmoteMapperPlugin


class RuleBasedEmoteMapperPlugin(EmoteMapperPlugin):
    plugin_id = "sweetiebot.emotes.rule_based"

    def __init__(self) -> None:
        self.config = {}

    def manifest(self) -> Dict[str, object]:
        base = super().manifest()
        base["capabilities"] = ["map_emote"]
        return base

    def map_emote(
        self,
        *,
        current_mood: str,
        dialogue_intent: Optional[str] = None,
        suggested_emote_id: Optional[str] = None,
        behavior_action: Optional[str] = None,
        safe_mode: bool = False,
        degraded_mode: bool = False,
    ) -> EmoteSelection:
        if safe_mode or degraded_mode:
            return EmoteSelection(
                emote_id="calm_neutral",
                reason="safe_or_degraded_mode",
                intensity=0.2,
                source=self.plugin_id,
                confidence=0.98,
            )

        if suggested_emote_id:
            return EmoteSelection(
                emote_id=suggested_emote_id,
                reason="dialogue_or_behavior_suggested",
                intensity=0.8,
                source=self.plugin_id,
                confidence=0.9,
                metadata={"suggested_emote_id": suggested_emote_id},
            )

        if dialogue_intent == "greet":
            return EmoteSelection(
                emote_id="warm_smile",
                reason="greeting_intent",
                intensity=0.8,
                source=self.plugin_id,
                confidence=0.88,
            )

        if dialogue_intent == "pose" or behavior_action == "routine":
            return EmoteSelection(
                emote_id="happy_pose",
                reason="pose_or_routine_behavior",
                intensity=0.85,
                source=self.plugin_id,
                confidence=0.86,
            )

        mood_map = {
            "calm": ("calm_neutral", 0.4),
            "warm": ("warm_smile", 0.65),
            "happy": ("happy_bounce", 0.8),
            "excited": ("happy_bounce", 0.95),
            "curious": ("curious_tilt", 0.7),
            "focused": ("focused_look", 0.6),
            "concerned": ("concerned_ears", 0.6),
            "startled": ("startled_blink", 0.9),
            "sleepy": ("sleepy_blink", 0.5),
        }

        emote_id, intensity = mood_map.get(current_mood, ("calm_neutral", 0.4))
        return EmoteSelection(
            emote_id=emote_id,
            reason="mood_mapping",
            intensity=float(intensity),
            source=self.plugin_id,
            confidence=0.8,
            metadata={"current_mood": current_mood},
        )

    def healthcheck(self) -> Dict[str, object]:
        return {
            "healthy": True,
            "plugin_id": self.plugin_id,
            "mode": "rule_based_local",
        }

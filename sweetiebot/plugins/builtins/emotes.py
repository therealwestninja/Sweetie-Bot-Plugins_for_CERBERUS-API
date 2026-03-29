from __future__ import annotations

from typing import Dict, Optional

from sweetiebot.plugins.base import EmoteMapperPlugin
from sweetiebot.plugins.manifest import PluginManifest
from sweetiebot.plugins.types import PluginType


class EmoteSelection:
    def __init__(self, emote_id: str, reason: str, intensity: float, source: str, confidence: float, metadata: dict | None = None) -> None:
        self.emote_id = emote_id
        self.reason = reason
        self.intensity = intensity
        self.source = source
        self.confidence = confidence
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "emote_id": self.emote_id,
            "reason": self.reason,
            "intensity": self.intensity,
            "source": self.source,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }


class RuleBasedEmoteMapperPlugin(EmoteMapperPlugin):
    plugin_id = "sweetiebot.emotes.rule_based"

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self.plugin_id,
            plugin_type=PluginType.EMOTE_MAPPER,
            display_name="Rule Based Emote Mapper",
            capabilities=["map_emote"],
        )

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
            return EmoteSelection("calm_neutral", "safe_or_degraded_mode", 0.2, self.plugin_id, 0.98)
        if suggested_emote_id:
            return EmoteSelection(suggested_emote_id, "dialogue_or_behavior_suggested", 0.8, self.plugin_id, 0.9)
        if dialogue_intent == "greet":
            return EmoteSelection("warm_smile", "greeting_intent", 0.8, self.plugin_id, 0.88)
        if dialogue_intent == "pose" or behavior_action == "routine":
            return EmoteSelection("happy_pose", "pose_or_routine_behavior", 0.85, self.plugin_id, 0.86)
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
        return EmoteSelection(emote_id, "mood_mapping", float(intensity), self.plugin_id, 0.8)

    def healthcheck(self) -> Dict[str, object]:
        return {"healthy": True, "plugin_id": self.plugin_id, "mode": "rule_based_local"}

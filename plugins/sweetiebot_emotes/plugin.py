from __future__ import annotations


class SweetieBotEmotesPlugin:
    name = "sweetiebot_emotes"

    def describe(self) -> dict:
        return {
            "name": self.name,
            "category": "expression",
            "provides": ["mood to emote mapping", "accessory hints", "timing metadata"],
        }

    def select_emote(self, *, emote_mapper, mood: str, emote_id: str | None = None) -> dict:
        command = emote_mapper.for_mood(mood)
        selected_emote = emote_id or command.emote_id
        payload = {
            "emote_id": selected_emote,
            "duration_ms": command.duration_ms,
            "mood": mood,
        }
        if command.accessories:
            payload["accessories"] = command.accessories
        return payload

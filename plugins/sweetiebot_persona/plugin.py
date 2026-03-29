from __future__ import annotations

from sweetiebot.character.schemas import CharacterState, MoodState


class SweetieBotPersonaPlugin:
    """Reusable persona selection and mood shaping helper."""

    name = "sweetiebot_persona"

    def describe(self) -> dict:
        return {
            "name": self.name,
            "category": "persona",
            "provides": [
                "persona selection",
                "mood shaping",
                "display metadata",
                "default expression profile",
                "routine preferences",
            ],
        }

    def list_personas(self, persona_catalog: dict[str, dict]) -> list[dict]:
        return [self.profile_for(persona) for persona in persona_catalog.values()]

    def profile_for(self, persona: dict) -> dict:
        defaults = persona.get("defaults", {})
        return {
            "id": persona["id"],
            "display_name": persona.get("display_name", persona["id"]),
            "traits": persona.get("traits", {}),
            "dialogue_style": persona.get("dialogue_style", {}),
            "motion_style": persona.get("motion_style", {}),
            "safety_profile": persona.get("safety_profile", "unknown"),
            "default_emote": defaults.get("emote", self._fallback_emote(persona)),
            "default_accessory_scene": defaults.get("accessory_scene"),
            "routine_tags": persona.get("routine_tags", []),
        }

    def select_persona(
        self,
        *,
        persona_catalog: dict[str, dict],
        persona_id: str,
        dialogue_manager,
        character: CharacterState,
    ) -> dict:
        persona = persona_catalog.get(persona_id)
        if not persona:
            raise KeyError(persona_id)

        profile = self.profile_for(persona)
        character.persona_id = persona_id
        character.active_emote = profile["default_emote"]
        character.active_accessory_scene = profile["default_accessory_scene"]
        dialogue_manager.configure_persona(persona)
        character.mood = self._derive_mood(persona)
        return {
            "persona": profile,
            "character": self._character_payload(character),
        }

    def _fallback_emote(self, persona: dict) -> str:
        energy_bias = persona.get("motion_style", {}).get("energy_bias", "gentle")
        return "happy_bounce" if energy_bias == "showy" else "curious_headtilt"

    def _derive_mood(self, persona: dict) -> MoodState:
        energy_bias = persona.get("motion_style", {}).get("energy_bias", "gentle")
        if energy_bias == "showy":
            return MoodState.EXCITED
        if energy_bias == "calm":
            return MoodState.HAPPY
        return MoodState.CURIOUS

    def _character_payload(self, character: CharacterState) -> dict:
        return {
            "persona_id": character.persona_id,
            "mood": character.mood.value,
            "attention_target": character.attention_target,
            "active_routine": character.active_routine,
            "is_speaking": character.is_speaking,
            "active_emote": character.active_emote,
            "active_accessory_scene": character.active_accessory_scene,
        }

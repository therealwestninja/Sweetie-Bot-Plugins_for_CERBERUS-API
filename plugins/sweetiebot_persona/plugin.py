from __future__ import annotations

from sweetiebot.character.schemas import CharacterState, MoodState


class SweetieBotPersonaPlugin:
    """Reusable persona selection and mood shaping helper.

    This plugin is designed to be easy to transplant into a CERBERUS-style
    plugin host: it accepts plain dictionaries for persona assets and returns
    plain dictionaries describing the resulting state change.
    """

    name = "sweetiebot_persona"

    def describe(self) -> dict:
        return {
            "name": self.name,
            "category": "persona",
            "provides": ["persona selection", "mood shaping", "display metadata"],
        }

    def list_personas(self, persona_catalog: dict[str, dict]) -> list[dict]:
        personas: list[dict] = []
        for persona in persona_catalog.values():
            personas.append(
                {
                    "id": persona["id"],
                    "display_name": persona.get("display_name", persona["id"]),
                    "dialogue_style": persona.get("dialogue_style", {}),
                    "motion_style": persona.get("motion_style", {}),
                    "safety_profile": persona.get("safety_profile", "unknown"),
                }
            )
        return personas

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

        character.persona_id = persona_id
        dialogue_manager.configure_persona(persona)
        character.mood = self._derive_mood(persona)
        return {
            "persona": persona,
            "character": self._character_payload(character),
        }

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
        }

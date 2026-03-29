from __future__ import annotations


class SweetieBotRoutinesPlugin:
    name = "sweetiebot_routines"

    def describe(self) -> dict:
        return {
            "name": self.name,
            "category": "choreography",
            "provides": ["routine lookup", "routine start metadata", "step summaries"],
        }

    def start_routine(
        self, *, routine_registry, persona_machine, character, routine_id: str
    ) -> dict:
        routine = routine_registry.get(routine_id)
        if not routine:
            raise KeyError(routine_id)

        character.active_routine = routine_id
        character.mood = persona_machine.transition("music")
        return {
            "routine_id": routine_id,
            "title": routine.get("title", routine_id),
            "steps": routine.get("steps", []),
            "step_count": len(routine.get("steps", [])),
            "character": {
                "persona_id": character.persona_id,
                "mood": character.mood.value,
                "attention_target": character.attention_target,
                "active_routine": character.active_routine,
                "is_speaking": character.is_speaking,
            },
        }

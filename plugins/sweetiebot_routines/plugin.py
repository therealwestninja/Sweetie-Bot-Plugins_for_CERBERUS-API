from __future__ import annotations


class SweetieBotRoutinesPlugin:
    name = "sweetiebot_routines"

    def describe(self) -> dict:
        return {
            "name": self.name,
            "category": "choreography",
            "provides": [
                "routine lookup",
                "routine planning",
                "routine start metadata",
                "step summaries",
                "capability hints",
            ],
        }

    def plan_routine(self, *, routine_registry, persona: dict, routine_id: str) -> dict:
        routine = routine_registry.get(routine_id)
        if not routine:
            raise KeyError(routine_id)
        defaults = persona.get("defaults", {})
        estimated_duration_ms = 0
        planned_steps = []
        for index, step in enumerate(routine.get("steps", []), start=1):
            planned = dict(step)
            planned.setdefault("step_index", index)
            planned.setdefault("type", "noop")
            if planned["type"] == "emote":
                planned.setdefault("id", defaults.get("emote", "curious_headtilt"))
                planned.setdefault("duration_ms", 1500)
            elif planned["type"] == "say":
                planned.setdefault("estimated_duration_ms", 2500)
            elif planned["type"] == "focus":
                planned.setdefault("estimated_duration_ms", 600)
            step_duration = planned.get(
                "duration_ms",
                planned.get("estimated_duration_ms", 1000),
            )
            estimated_duration_ms += step_duration
            planned_steps.append(planned)

        return {
            "routine_id": routine_id,
            "title": routine.get("title", routine_id),
            "step_count": len(planned_steps),
            "estimated_duration_ms": estimated_duration_ms,
            "required_capabilities": routine.get("required_capabilities", []),
            "cancellation_behavior": routine.get("cancellation_behavior", "safe_idle"),
            "persona_defaults": {
                "default_emote": defaults.get("emote", "curious_headtilt"),
                "default_accessory_scene": defaults.get("accessory_scene"),
            },
            "steps": planned_steps,
        }

    def start_routine(
        self,
        *,
        routine_registry,
        persona_machine,
        character,
        persona: dict,
        routine_id: str,
    ) -> dict:
        plan = self.plan_routine(
            routine_registry=routine_registry,
            persona=persona,
            routine_id=routine_id,
        )
        character.active_routine = routine_id
        character.mood = persona_machine.transition("music")
        return {
            **plan,
            "character": {
                "persona_id": character.persona_id,
                "mood": character.mood.value,
                "attention_target": character.attention_target,
                "active_routine": character.active_routine,
                "is_speaking": character.is_speaking,
                "active_emote": character.active_emote,
                "active_accessory_scene": character.active_accessory_scene,
            },
        }

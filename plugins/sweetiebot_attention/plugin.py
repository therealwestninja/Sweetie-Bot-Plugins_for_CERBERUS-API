from __future__ import annotations

from sweetiebot.perception.attention_manager import AttentionTarget


class SweetieBotAttentionPlugin:
    name = "sweetiebot_attention"

    def describe(self) -> dict:
        return {
            "name": self.name,
            "category": "perception",
            "provides": ["attention target updates", "social target summaries"],
        }

    def focus(
        self,
        *,
        attention_manager,
        character,
        target_id: str,
        confidence: float = 1.0,
        mode: str = "person",
    ) -> dict:
        attention_manager.update(
            AttentionTarget(id=target_id, kind=mode, confidence=confidence)
        )
        character.attention_target = target_id
        return {
            "target_id": target_id,
            "confidence": confidence,
            "mode": mode,
            "character": {
                "persona_id": character.persona_id,
                "mood": character.mood.value,
                "attention_target": character.attention_target,
                "active_routine": character.active_routine,
                "is_speaking": character.is_speaking,
            },
        }

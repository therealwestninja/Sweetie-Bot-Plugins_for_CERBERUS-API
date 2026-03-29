from __future__ import annotations

from sweetiebot.character.intent_types import IntentType


class SweetieBotDialoguePlugin:
    name = "sweetiebot_dialogue"

    def describe(self) -> dict:
        return {
            "name": self.name,
            "category": "dialogue",
            "provides": ["reply generation", "intent tagging", "mood triggers"],
        }

    def handle_text(self, *, text: str, dialogue_manager, persona_machine, character) -> dict:
        reply = dialogue_manager.reply_for(text)
        character.is_speaking = True
        trigger_map = {
            IntentType.GREET: "praised",
            IntentType.SPEAK: "music" if "sing" in text.lower() else "praised",
        }
        character.mood = persona_machine.transition(trigger_map.get(reply.intent, "praised"))
        return {
            "heard": text,
            "reply": reply.text,
            "intent": reply.intent.value,
            "emote_id": reply.emote_id,
            "character": {
                "persona_id": character.persona_id,
                "mood": character.mood.value,
                "attention_target": character.attention_target,
                "active_routine": character.active_routine,
                "is_speaking": character.is_speaking,
            },
        }

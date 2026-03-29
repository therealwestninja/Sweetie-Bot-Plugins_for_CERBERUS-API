from dataclasses import dataclass

from sweetiebot.character.intent_types import IntentType


@dataclass
class DialogueReply:
    intent: IntentType
    text: str
    emote_id: str | None = None


class DialogueManager:
    def __init__(self) -> None:
        self.persona_id = "sweetiebot_default"
        self.dialogue_style: dict[str, str] = {
            "tone": "warm",
            "pacing": "lively",
            "verbosity": "concise",
        }

    def configure_persona(self, persona: dict) -> None:
        self.persona_id = persona.get("id", self.persona_id)
        self.dialogue_style = persona.get("dialogue_style", self.dialogue_style)

    def _greeting_text(self) -> str:
        tone = self.dialogue_style.get("tone", "warm")
        if self.persona_id == "sweetiebot_convention" or tone == "bright":
            return "Hi everypony! Show mode is live and I am ready to sparkle."
        if self.persona_id == "sweetiebot_companion" or tone == "gentle":
            return "Hi there. I am right here with you, nice and easy."
        return "Hi there! I am ready whenever you are."

    def _default_text(self) -> str:
        tone = self.dialogue_style.get("tone", "warm")
        if self.persona_id == "sweetiebot_convention" or tone == "bright":
            return "I am still learning, but I can keep the energy up and stay on cue."
        if self.persona_id == "sweetiebot_companion" or tone == "gentle":
            return "I am still learning, but I am listening carefully and staying close."
        return "I am still learning, but I am paying attention."

    def reply_for(self, user_text: str) -> DialogueReply:
        lowered = user_text.lower()
        if "hello" in lowered or "hi" in lowered:
            return DialogueReply(
                IntentType.GREET,
                self._greeting_text(),
                "curious_headtilt",
            )
        return DialogueReply(
            IntentType.SPEAK,
            self._default_text(),
            "curious_headtilt",
        )

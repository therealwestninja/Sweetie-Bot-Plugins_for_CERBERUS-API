from dataclasses import dataclass

from sweetiebot.character.intent_types import IntentType


@dataclass
class DialogueReply:
    intent: IntentType
    text: str
    emote_id: str | None = None


class DialogueManager:
    def reply_for(self, user_text: str) -> DialogueReply:
        lowered = user_text.lower()
        if "hello" in lowered or "hi" in lowered:
            return DialogueReply(
                IntentType.GREET,
                "Hi there! I'm ready whenever you are.",
                "curious_headtilt",
            )
        return DialogueReply(
            IntentType.SPEAK,
            "I'm still learning, but I'm paying attention.",
            "curious_headtilt",
        )

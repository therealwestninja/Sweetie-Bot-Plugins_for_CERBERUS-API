from __future__ import annotations

from dataclasses import asdict, dataclass, field

from sweetiebot.character.intent_types import IntentType

MAX_SPOKEN_CHARS = 240


@dataclass(slots=True)
class DialogueDirective:
    emote_id: str | None = None
    routine_id: str | None = None
    accessory_scene_id: str | None = None
    operator_note: str | None = None


@dataclass(slots=True)
class DialogueReply:
    intent: IntentType
    text: str
    directive: DialogueDirective = field(default_factory=DialogueDirective)
    confidence: float = 0.75
    fallback_mode: bool = False

    def normalized(self) -> "DialogueReply":
        text = " ".join(self.text.split()).strip()
        if not text:
            text = "I am here and ready."
        if len(text) > MAX_SPOKEN_CHARS:
            text = text[: MAX_SPOKEN_CHARS - 1].rstrip() + "…"
        confidence = min(max(self.confidence, 0.0), 1.0)
        return DialogueReply(
            intent=self.intent,
            text=text,
            directive=self.directive,
            confidence=confidence,
            fallback_mode=self.fallback_mode,
        )

    def to_dict(self) -> dict[str, object]:
        reply = self.normalized()
        payload = asdict(reply)
        payload["intent"] = reply.intent.value
        return payload

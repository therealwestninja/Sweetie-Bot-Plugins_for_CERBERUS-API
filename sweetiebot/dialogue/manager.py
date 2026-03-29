from __future__ import annotations

from dataclasses import dataclass, field

from sweetiebot.character.intent_types import IntentType
from sweetiebot.dialogue.contracts import DialogueDirective, DialogueReply

DEFAULT_DIALOGUE_STYLE = {
    "tone": "warm",
    "pacing": "lively",
    "verbosity": "concise",
}

DEFAULT_LIMITS = {
    "max_spoken_chars": 220,
    "physical_claims": "never imply motion happened unless control confirmed it",
    "safety": "no direct actuator control",
}


@dataclass(slots=True)
class PersonaRules:
    persona_id: str = "sweetiebot_default"
    dialogue_style: dict[str, str] = field(default_factory=lambda: DEFAULT_DIALOGUE_STYLE.copy())
    speaking_rules: list[str] = field(default_factory=list)
    preferred_greeting: str | None = None
    default_emote: str = "curious_headtilt"
    default_routine: str | None = None
    default_accessory_scene: str | None = None
    limits: dict[str, object] = field(default_factory=lambda: DEFAULT_LIMITS.copy())


class DialogueManager:
    def __init__(self) -> None:
        self.rules = PersonaRules()

    @property
    def persona_id(self) -> str:
        return self.rules.persona_id

    def configure_persona(self, persona: dict) -> None:
        defaults = persona.get("defaults", {}) or {}
        self.rules = PersonaRules(
            persona_id=persona.get("id", self.rules.persona_id),
            dialogue_style={**DEFAULT_DIALOGUE_STYLE, **(persona.get("dialogue_style", {}) or {})},
            speaking_rules=list(persona.get("speaking_rules", []) or []),
            preferred_greeting=persona.get("preferred_greeting"),
            default_emote=defaults.get("emote", self.rules.default_emote),
            default_routine=defaults.get("routine", self.rules.default_routine),
            default_accessory_scene=defaults.get(
                "accessory_scene", self.rules.default_accessory_scene
            ),
            limits={**DEFAULT_LIMITS, **(persona.get("limits", {}) or {})},
        )

    def build_system_prompt(self) -> str:
        tone = self.rules.dialogue_style["tone"]
        pacing = self.rules.dialogue_style["pacing"]
        verbosity = self.rules.dialogue_style["verbosity"]
        speaking_rules = self.rules.speaking_rules or [
            "Keep spoken replies easy to perform on-stage.",
            "Sound cute, competent, and reassuring.",
        ]
        bullet_rules = " ".join(f"- {rule}" for rule in speaking_rules)
        return (
            "You are Sweetie Bot, a safety-conscious stage-and-companion robot. "
            f"Tone: {tone}. Pacing: {pacing}. Verbosity: {verbosity}. "
            f"Speech limit: {self.rules.limits['max_spoken_chars']} chars. "
            "Never claim hardware actions already happened unless confirmed by control systems. "
            f"Core constraints: {self.rules.limits['safety']}. "
            f"Speaking rules: {bullet_rules}"
        )

    def infer_intent(self, user_text: str) -> IntentType:
        lowered = user_text.lower()
        if any(token in lowered for token in ["cancel", "stop", "quiet", "enough"]):
            return IntentType.CANCEL
        if any(token in lowered for token in ["hello", "hi", "hey"]):
            return IntentType.GREET
        if any(token in lowered for token in ["routine", "pose", "wave", "dance", "photo"]):
            return IntentType.ROUTINE
        return IntentType.SPEAK

    def choose_emote(self, user_text: str, reply_text: str) -> str:
        lowered = f"{user_text} {reply_text}".lower()
        if any(token in lowered for token in ["song", "music", "yay", "sparkle"]):
            return "happy_bounce"
        if any(token in lowered for token in ["sorry", "apolog", "oops"]):
            return "bashful_ears_low"
        if any(token in lowered for token in ["photo", "pose", "camera"]):
            return "happy_pose"
        return self.rules.default_emote

    def suggest_routine(self, user_text: str) -> str | None:
        lowered = user_text.lower()
        if any(token in lowered for token in ["photo", "pose", "camera"]):
            return "photo_pose"
        if any(token in lowered for token in ["wave", "hello", "greet"]):
            return "greet_guest"
        if any(token in lowered for token in ["idle", "cute", "wait"]):
            return "idle_cute"
        return self.rules.default_routine

    def _greeting_text(self) -> str:
        if self.rules.preferred_greeting:
            return self.rules.preferred_greeting
        tone = self.rules.dialogue_style.get("tone", "warm")
        if self.persona_id == "sweetiebot_convention" or tone == "bright":
            return "Hi everypony! Show mode is live and I am ready to sparkle."
        if self.persona_id == "sweetiebot_companion" or tone == "gentle":
            return "Hi there. I am right here with you, nice and easy."
        return "Hi there! I am ready whenever you are."

    def _song_text(self) -> str:
        if self.persona_id == "sweetiebot_convention":
            return "Cue the music! I can warm up with a happy little bounce."
        if self.persona_id == "sweetiebot_companion":
            return "I can do a soft little song intro and stay close to you."
        return "I can do a cheerful song intro when you are ready."

    def _thanks_text(self) -> str:
        if self.persona_id == "sweetiebot_convention":
            return "Aww, thank you! I will keep the energy bright and tidy."
        if self.persona_id == "sweetiebot_companion":
            return "Thank you. I like being helpful and gentle."
        return "Thank you! I am doing my very best."

    def _cancel_text(self) -> str:
        return "Okay. I am stopping and returning to a calm neutral state."

    def _default_text(self) -> str:
        tone = self.rules.dialogue_style.get("tone", "warm")
        if self.persona_id == "sweetiebot_convention" or tone == "bright":
            return "I am still learning, but I can keep the energy up and stay on cue."
        if self.persona_id == "sweetiebot_companion" or tone == "gentle":
            return "I am still learning, but I am listening carefully and staying close."
        return "I am still learning, but I am paying attention."

    def reply_for(self, user_text: str) -> DialogueReply:
        lowered = user_text.lower()
        intent = self.infer_intent(user_text)

        if intent is IntentType.CANCEL:
            text = self._cancel_text()
        elif any(token in lowered for token in ["sing", "song", "music"]):
            text = self._song_text()
        elif any(token in lowered for token in ["thanks", "thank you", "good bot"]):
            text = self._thanks_text()
        elif intent is IntentType.GREET:
            text = self._greeting_text()
        else:
            text = self._default_text()

        directive = DialogueDirective(
            emote_id=self.choose_emote(user_text, text),
            routine_id=self.suggest_routine(user_text) if intent is not IntentType.CANCEL else "return_to_neutral",
            accessory_scene_id=self.rules.default_accessory_scene,
            operator_note="Generated by local Sweetie Bot dialogue manager.",
        )
        return DialogueReply(
            intent=intent,
            text=text,
            directive=directive,
            confidence=0.9 if intent is IntentType.GREET else 0.78,
            fallback_mode=False,
        ).normalized()

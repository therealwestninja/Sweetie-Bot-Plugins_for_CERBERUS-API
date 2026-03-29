from dataclasses import dataclass
from enum import StrEnum


class MoodState(StrEnum):
    CURIOUS = "curious"
    HAPPY = "happy"
    BASHFUL = "bashful"
    APOLOGETIC = "apologetic"
    EXCITED = "excited"
    PROTECTIVE = "protective"
    SLEEPY = "sleepy"


@dataclass
class CharacterState:
    persona_id: str
    mood: MoodState
    attention_target: str | None
    active_routine: str | None
    is_speaking: bool
    active_emote: str | None = None
    active_accessory_scene: str | None = None

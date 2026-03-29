from enum import StrEnum


class IntentType(StrEnum):
    GREET = "greet"
    FOCUS = "focus"
    EMOTE = "emote"
    SPEAK = "speak"
    ROUTINE = "routine"
    CANCEL = "cancel"

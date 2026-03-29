from dataclasses import asdict
from sweetiebot.character.schemas import CharacterState, MoodState


def get_character() -> dict:
    state = CharacterState(
        persona_id="sweetiebot_default",
        mood=MoodState.CURIOUS,
        attention_target=None,
        active_routine=None,
        is_speaking=False,
    )
    return asdict(state)

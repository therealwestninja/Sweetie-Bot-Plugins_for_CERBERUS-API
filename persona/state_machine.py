from sweetiebot.character.schemas import MoodState


class PersonaStateMachine:
    def __init__(self, default: MoodState = MoodState.CURIOUS) -> None:
        self.current = default

    def transition(self, trigger: str) -> MoodState:
        mapping = {
            "praised": MoodState.HAPPY,
            "surprised": MoodState.BASHFUL,
            "mistake": MoodState.APOLOGETIC,
            "music": MoodState.EXCITED,
            "low_battery": MoodState.SLEEPY,
        }
        self.current = mapping.get(trigger, self.current)
        return self.current

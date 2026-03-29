from dataclasses import dataclass


@dataclass
class EmoteCommand:
    emote_id: str
    duration_ms: int = 1500


class EmoteMapper:
    def for_mood(self, mood: str) -> EmoteCommand:
        mapping = {
            "curious": EmoteCommand("curious_headtilt", 1800),
            "happy": EmoteCommand("happy_bounce", 1600),
            "bashful": EmoteCommand("bashful_shift", 1400),
        }
        return mapping.get(mood, EmoteCommand("curious_headtilt"))

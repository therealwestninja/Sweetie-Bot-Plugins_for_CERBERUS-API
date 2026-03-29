class MemoryStore:
    def __init__(self) -> None:
        self._memory = {
            "known_people": [],
            "preferences": [],
        }

    def summary(self) -> dict:
        return dict(self._memory)

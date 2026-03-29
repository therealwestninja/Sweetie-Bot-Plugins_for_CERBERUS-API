class RoutineRegistry:
    def __init__(self) -> None:
        self._routines: dict[str, dict] = {}

    def register(self, routine_id: str, payload: dict) -> None:
        self._routines[routine_id] = payload

    def get(self, routine_id: str) -> dict | None:
        return self._routines.get(routine_id)

    def list_ids(self) -> list[str]:
        return sorted(self._routines)

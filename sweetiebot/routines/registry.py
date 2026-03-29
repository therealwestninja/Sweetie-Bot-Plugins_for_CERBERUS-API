from __future__ import annotations

from pathlib import Path

import yaml


class RoutineRegistry:
    def __init__(self) -> None:
        self._routines: dict[str, dict] = {}

    def register(self, routine_id: str, payload: dict) -> None:
        self._routines[routine_id] = payload

    def register_from_yaml(self, path: str | Path) -> None:
        with open(path, "r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        routine_id = payload.get("id") or Path(path).stem
        payload.setdefault("id", routine_id)
        payload.setdefault("title", routine_id)
        payload.setdefault("steps", [])
        self.register(routine_id, payload)

    def get(self, routine_id: str) -> dict | None:
        return self._routines.get(routine_id)

    def list_ids(self) -> list[str]:
        return sorted(self._routines)

    def list_all(self) -> list[dict]:
        return [self._routines[key] for key in sorted(self._routines)]

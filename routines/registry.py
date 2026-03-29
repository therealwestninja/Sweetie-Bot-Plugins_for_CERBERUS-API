from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sweetiebot.routines.models import RoutineModel


class RoutineRegistry:
    def __init__(self) -> None:
        self._routines: dict[str, dict[str, Any]] = {}

    def register(self, routine_id: str, payload: dict[str, Any]) -> None:
        normalized = self._normalize(routine_id, payload)
        self._routines[routine_id] = normalized

    def register_from_yaml(self, path: str | Path) -> None:
        file_path = Path(path)
        payload = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
        routine_id = file_path.stem
        self.register(routine_id, dict(payload))

    def list_ids(self) -> list[str]:
        return sorted(self._routines)

    def get(self, routine_id: str) -> dict[str, Any] | None:
        routine = self._routines.get(routine_id)
        return dict(routine) if routine else None

    def _normalize(self, routine_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        title = payload.get("title") or routine_id.replace("_", " ").title()
        summary = payload.get("summary") or payload.get("description") or ""
        steps = payload.get("steps") or []
        normalized_steps: list[dict[str, Any]] = []
        total_duration = 0
        for raw in steps:
            if isinstance(raw, dict) and "type" in raw:
                step_type = raw["type"]
                value = raw.get("value")
                duration = int(raw.get("duration_ms", self._estimate_duration(step_type, value)))
            elif isinstance(raw, dict) and len(raw) == 1:
                step_type, value = next(iter(raw.items()))
                step_type = "pause" if step_type == "pause_ms" else step_type
                duration = self._estimate_duration(step_type, value)
            else:
                continue
            total_duration += duration
            normalized_steps.append({
                "type": step_type,
                "value": value,
                "duration_ms": duration,
                "step_index": len(normalized_steps) + 1,
            })
        return {
            "routine_id": routine_id,
            "title": title,
            "summary": summary,
            "steps": normalized_steps,
            "step_count": len(normalized_steps),
            "estimated_duration_ms": total_duration,
            "interruptible": bool(payload.get("interruptible", True)),
        }

    def _estimate_duration(self, step_type: str, value: Any) -> int:
        if step_type == "speak":
            return max(1500, min(len(str(value or "")) * 60, 4000))
        if step_type == "emote":
            return 600
        if step_type == "focus":
            return 300
        if step_type == "pause":
            return int(value or 500)
        return 500


def load_routines_file(path: str | Path) -> list[RoutineModel]:
    file_path = Path(path)
    data: Any = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
    routines = data.get("routines", [])
    result = []
    for item in routines:
        result.append(RoutineModel.model_validate(item))
    return result

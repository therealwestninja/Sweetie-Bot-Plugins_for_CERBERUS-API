from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class RoutineRegistry:
    def __init__(self) -> None:
        self._routines: dict[str, dict[str, Any]] = {}

    def register(self, routine_id: str, payload: dict[str, Any]) -> None:
        self._routines[routine_id] = self._normalize(payload, fallback_id=routine_id)

    def register_from_yaml(self, path: str | Path) -> None:
        with open(path, "r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        routine_id = payload.get("id") or Path(path).stem
        self.register(routine_id, payload)

    def _normalize(self, payload: dict[str, Any], *, fallback_id: str) -> dict[str, Any]:
        routine_id = payload.get("id") or fallback_id
        steps = [self._normalize_step(step) for step in list(payload.get("steps") or [])]
        estimated = payload.get("estimated_duration_ms")
        if estimated is None:
            estimated = sum(step.get("duration_ms", 800) for step in steps) or 800
        return {
            "id": routine_id,
            "title": payload.get("title", routine_id.replace("_", " ").title()),
            "summary": payload.get("summary", ""),
            "interruptible": bool(payload.get("interruptible", True)),
            "safe_neutral_on_cancel": bool(payload.get("safe_neutral_on_cancel", True)),
            "required_capabilities": list(payload.get("required_capabilities") or []),
            "tags": list(payload.get("tags") or []),
            "steps": steps,
            "step_count": len(steps),
            "estimated_duration_ms": int(estimated),
        }

    def _normalize_step(self, step: dict[str, Any]) -> dict[str, Any]:
        if "type" not in step:
            if "speak" in step:
                step = {"type": "speak", "text": step["speak"]}
            elif "emote" in step:
                step = {"type": "emote", "emote_id": step["emote"]}
            elif "pause_ms" in step:
                step = {"type": "pause", "duration_ms": step["pause_ms"]}
            else:
                step = {"type": "custom", **step}
        step = dict(step)
        if step["type"] == "pause":
            step.setdefault("duration_ms", 500)
        elif step["type"] == "speak":
            step.setdefault("duration_ms", max(900, len(step.get("text", "")) * 35))
        else:
            step.setdefault("duration_ms", 800)
        return step

    def get(self, routine_id: str) -> dict[str, Any] | None:
        return self._routines.get(routine_id)

    def list_ids(self) -> list[str]:
        return sorted(self._routines)

    def list_all(self) -> list[dict[str, Any]]:
        return [self._routines[key] for key in sorted(self._routines)]

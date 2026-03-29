from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_DIALOGUE_STYLE = {
    "tone": "warm",
    "pacing": "lively",
    "verbosity": "concise",
}


class PersonaValidationError(ValueError):
    pass


def load_persona(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return validate_persona(data, source=Path(path))


def validate_persona(data: dict[str, Any], *, source: Path | None = None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise PersonaValidationError("Persona payload must be a mapping.")
    persona_id = str(data.get("id", "")).strip()
    if not persona_id:
        location = f" in {source}" if source else ""
        raise PersonaValidationError(f"Persona is missing required field 'id'{location}.")

    defaults = dict(data.get("defaults") or {})
    dialogue_style = {**DEFAULT_DIALOGUE_STYLE, **(data.get("dialogue_style") or {})}

    normalized = {
        **data,
        "id": persona_id,
        "display_name": data.get("display_name", persona_id.replace("_", " ").title()),
        "dialogue_style": dialogue_style,
        "speaking_rules": list(data.get("speaking_rules") or []),
        "traits": dict(data.get("traits") or {}),
        "defaults": {
            "emote": defaults.get("emote", "curious_headtilt"),
            "accessory_scene": defaults.get("accessory_scene"),
            "routine": defaults.get("routine"),
        },
        "limits": {
            "max_spoken_chars": int((data.get("limits") or {}).get("max_spoken_chars", 220)),
            "safety": (data.get("limits") or {}).get(
                "safety", "no direct actuator control"
            ),
        },
    }
    return normalized

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sweetiebot.persona.models import PersonaModel


class PersonaValidationError(ValueError):
    pass


DEFAULT_PERSONA = {
    "id": "sweetiebot_default",
    "dialogue_style": {"tone": "warm", "pacing": "lively", "verbosity": "concise"},
    "defaults": {"emote": "curious_headtilt", "routine": None, "accessory_scene": "eyes_curious"},
    "preferred_greeting": "Hi there! I'm Sweetie Bot!",
}


PERSONA_LIBRARY = {
    "sweetiebot_default": DEFAULT_PERSONA,
    "sweetiebot_convention": {
        "id": "sweetiebot_convention",
        "dialogue_style": {"tone": "bright", "pacing": "showtime", "verbosity": "concise"},
        "defaults": {"emote": "happy_bounce", "routine": "greet_guest", "accessory_scene": "eyes_showtime"},
        "preferred_greeting": "Hi everypony! Sparkle stations are ready.",
    },
    "sweetiebot_companion": {
        "id": "sweetiebot_companion",
        "dialogue_style": {"tone": "gentle", "pacing": "calm", "verbosity": "concise"},
        "defaults": {"emote": "warm_smile", "routine": None, "accessory_scene": "eyes_soft"},
        "preferred_greeting": "Hi there. I'm right here with you.",
    },
}


def validate_persona(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise PersonaValidationError("Persona payload must be a mapping")
    persona_id = payload.get("id") or payload.get("persona_id")
    if not persona_id:
        raise PersonaValidationError("Persona id is required")
    defaults = dict(DEFAULT_PERSONA)
    defaults["dialogue_style"] = dict(DEFAULT_PERSONA["dialogue_style"])
    defaults["defaults"] = dict(DEFAULT_PERSONA["defaults"])
    merged = {**defaults, **payload, "id": str(persona_id)}
    merged["dialogue_style"] = {**DEFAULT_PERSONA["dialogue_style"], **dict(payload.get("dialogue_style") or {})}
    merged["defaults"] = {**DEFAULT_PERSONA["defaults"], **dict(payload.get("defaults") or {})}
    return merged


def load_persona(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    try:
        data: Any = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise PersonaValidationError(f"Persona file not found: {file_path}") from exc
    return validate_persona(dict(data))


class SimplePersonaFile:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.persona_id = payload["id"]
        self.display_name = payload.get("display_name", "Sweetie Bot")
        self.default_emote = payload.get("defaults", {}).get("emote", "curious_headtilt")
        self.speaking_style = payload.get("dialogue_style", {}).get("tone", "warm")
        self.fallback_lines = [payload.get("preferred_greeting", "Hi there!")]


def load_persona_file(path: str | Path) -> PersonaModel | SimplePersonaFile:
    payload = load_persona(path)
    model_payload = {
        "persona_id": payload["id"],
        "display_name": payload.get("display_name", "Sweetie Bot"),
        "speaking_style": payload.get("dialogue_style", {}).get("tone", "warm"),
        "default_emote": payload.get("defaults", {}).get("emote", "curious_headtilt"),
        "fallback_lines": [payload.get("preferred_greeting", "Hi there!")],
    }
    return PersonaModel.model_validate(model_payload)

from pathlib import Path

import pytest

from sweetiebot.persona.loader import PersonaValidationError, load_persona, validate_persona


def test_validate_persona_adds_defaults() -> None:
    persona = validate_persona({"id": "sweetiebot_default"})
    assert persona["dialogue_style"]["tone"] == "warm"
    assert persona["defaults"]["emote"] == "curious_headtilt"


def test_load_persona_from_yaml(tmp_path: Path) -> None:
    path = tmp_path / "default.yaml"
    path.write_text("id: sweetiebot_default\n", encoding="utf-8")
    data = load_persona(path)
    assert data["id"] == "sweetiebot_default"


def test_missing_persona_id_raises() -> None:
    with pytest.raises(PersonaValidationError):
        validate_persona({})

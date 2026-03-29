from pathlib import Path

from sweetiebot.persona.loader import load_persona


def test_load_persona():
    path = Path("sweetiebot-assets/persona/default.yaml")
    data = load_persona(path)
    assert data["id"] == "sweetiebot_default"

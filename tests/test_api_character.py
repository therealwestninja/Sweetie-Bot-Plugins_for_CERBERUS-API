from fastapi.testclient import TestClient

from sweetiebot.api.app import create_app


def test_character_foundation_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/character/foundation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["persona_id"] == "sweetiebot_default"
    assert "dialogue_style" in payload


def test_character_say_endpoint_returns_structured_payload() -> None:
    client = TestClient(create_app())
    response = client.post("/character/say", json={"text": "hello"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"]["intent"] == "greet"
    assert "state" in payload
    assert "directive" in payload["reply"]


def test_character_plugins_endpoint_lists_builtin_plugins() -> None:
    client = TestClient(create_app())
    response = client.get("/character/plugins")
    assert response.status_code == 200
    payload = response.json()
    plugin_ids = {plugin["plugin_id"] for plugin in payload["plugins"]}
    assert "sweetiebot.local_dialogue" in plugin_ids
    assert "sweetiebot.demo_routines" in plugin_ids


def test_character_persona_endpoint_reconfigures_runtime() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/character/persona",
        json={
            "payload": {
                "id": "sweetiebot_convention",
                "dialogue_style": {"tone": "bright"},
                "defaults": {"emote": "happy_bounce"},
            }
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"]["persona_id"] == "sweetiebot_convention"
    assert payload["state"]["current_emote_id"] == "happy_bounce"

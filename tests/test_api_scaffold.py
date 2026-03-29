from fastapi.testclient import TestClient

from upstream_api.app.main import app

client = TestClient(app)


def test_root_and_character_state() -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "scaffold-online"
    assert payload["character"]["persona_id"] == "sweetiebot_default"


def test_say_updates_mood_and_returns_reply() -> None:
    response = client.post("/character/say", json={"text": "hello sweetie bot"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "greet"
    assert payload["emote_id"] == "curious_headtilt"


def test_routine_and_cancel_flow() -> None:
    response = client.post("/character/routine", json={"routine_id": "greeting_01"})
    assert response.status_code == 200
    assert response.json()["active"] == "greeting_01"

    cancel = client.post("/character/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["active_routine"] is None

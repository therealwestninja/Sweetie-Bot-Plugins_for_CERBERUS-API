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


def test_events_endpoint_and_websocket_stream() -> None:
    events_before = client.get("/events")
    assert events_before.status_code == 200
    assert "items" in events_before.json()

    with client.websocket_connect("/ws/events") as websocket:
        snapshot = websocket.receive_json()
        assert snapshot["type"] == "events.snapshot"
        assert snapshot["payload"]["character"]["persona_id"] == "sweetiebot_default"

        client.post(
            "/character/focus",
            json={"target_id": "guest-01", "confidence": 0.9, "mode": "person"},
        )
        event = websocket.receive_json()
        assert event["type"] == "attention.target_changed"
        assert event["payload"]["target_id"] == "guest-01"

from fastapi.testclient import TestClient

from sweetiebot.api.app import app


def test_dialogue_api_roundtrip():
    client = TestClient(app)

    res = client.get("/character/dialogue")
    assert res.status_code == 200
    assert "provider" in res.json()

    res2 = client.post("/character/dialogue/generate", json={"user_text": "hello there"})
    assert res2.status_code == 200
    payload = res2.json()
    assert payload["intent"] == "greet"
    assert payload["spoken_text"] == "Hi there!"

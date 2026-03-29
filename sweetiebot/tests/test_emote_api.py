from fastapi.testclient import TestClient

from sweetiebot.api.app import app


def test_emote_api_roundtrip():
    client = TestClient(app)

    res = client.get("/character/emotes")
    assert res.status_code == 200
    assert "mapper" in res.json()

    res2 = client.post("/character/emotes/map", json={"dialogue_intent": "greet"})
    assert res2.status_code == 200
    payload = res2.json()
    assert payload["emote_id"] == "warm_smile"

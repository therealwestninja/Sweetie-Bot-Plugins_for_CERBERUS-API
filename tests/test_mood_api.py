from fastapi.testclient import TestClient

from sweetiebot.api.app import app


def test_mood_api_roundtrip():
    client = TestClient(app)

    res = client.get("/character/mood")
    assert res.status_code == 200
    assert "current_mood" in res.json()

    res2 = client.post("/character/mood/event", json={"event": "greet"})
    assert res2.status_code == 200
    assert res2.json()["mood"] == "warm"

    res3 = client.post("/character/mood/decay")
    assert res3.status_code == 200
    assert "mood" in res3.json()

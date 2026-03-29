from fastapi.testclient import TestClient

from sweetiebot.api.app import app


def test_behavior_api_roundtrip():
    client = TestClient(app)

    res = client.get("/character/behavior")
    assert res.status_code == 200
    assert "director" in res.json()

    res2 = client.post("/character/behavior/suggest", json={"user_text": "hello there"})
    assert res2.status_code == 200
    payload = res2.json()
    assert payload["action"] == "routine"
    assert payload["routine_id"] == "greet_guest"

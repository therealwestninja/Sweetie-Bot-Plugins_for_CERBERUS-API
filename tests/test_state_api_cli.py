from fastapi.testclient import TestClient

from sweetiebot.api.app import app


def test_state_api_roundtrip():
    client = TestClient(app)
    res = client.post("/character/state", json={"mood": "curious", "focus_target": "guest"})
    assert res.status_code == 200
    payload = res.json()
    assert payload["mood"] == "curious"
    assert payload["focus_target"] == "guest"

    res2 = client.get("/character/state")
    assert res2.status_code == 200
    payload2 = res2.json()
    assert payload2["mood"] == "curious"

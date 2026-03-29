from fastapi.testclient import TestClient

from sweetiebot.api.app import app


def test_telemetry_api_roundtrip():
    client = TestClient(app)

    client.post("/character/mood/event", json={"event": "greet"})

    res = client.get("/character/telemetry")
    assert res.status_code == 200
    payload = res.json()
    assert "sink" in payload
    assert "recent_events" in payload

    res2 = client.get("/character/telemetry/events?limit=5")
    assert res2.status_code == 200
    assert "items" in res2.json()

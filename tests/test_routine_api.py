from fastapi.testclient import TestClient

from sweetiebot.api.app import app


def test_routine_arbitration_api():
    client = TestClient(app)

    res = client.get("/character/routines/arbitration")
    assert res.status_code == 200
    assert "active_cooldowns" in res.json()

    res2 = client.post("/character/routines/arbitrate", json={"requested_routine": "greet_guest"})
    assert res2.status_code == 200
    payload = res2.json()
    assert payload["routine_id"] == "greet_guest"
    assert payload["allowed"] is True

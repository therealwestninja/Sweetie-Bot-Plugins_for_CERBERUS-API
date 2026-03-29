from fastapi.testclient import TestClient

from sweetiebot.api.app import app


def test_perception_api_roundtrip():
    client = TestClient(app)

    res = client.get("/character/perception")
    assert res.status_code == 200
    payload = res.json()
    assert "sources" in payload

    res2 = client.post("/character/perception/poll")
    assert res2.status_code == 200
    assert "items" in res2.json()

    res3 = client.post("/character/perception/apply")
    assert res3.status_code == 200
    payload3 = res3.json()
    assert "observations" in payload3
    assert "state" in payload3

from fastapi.testclient import TestClient

from sweetiebot.api.app import app


def test_attention_api_roundtrip():
    client = TestClient(app)

    res = client.get("/character/attention")
    assert res.status_code == 200
    assert "current_focus" in res.json()

    res2 = client.post("/character/attention/suggest", json={"user_text": "hello there"})
    assert res2.status_code == 200
    assert "target" in res2.json()

    res3 = client.post("/character/attention/apply", json={"user_text": "photo over here"})
    assert res3.status_code == 200
    payload = res3.json()
    assert payload["suggestion"]["target"] == "camera"

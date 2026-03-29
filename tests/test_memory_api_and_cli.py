from fastapi.testclient import TestClient

from sweetiebot.api.app import app


def test_memory_api_roundtrip():
    client = TestClient(app)
    res = client.post("/character/memory/remember", json={
        "kind": "fact",
        "content": "Scootaloo visited the workshop",
        "source": "test",
        "scope": "session",
    })
    assert res.status_code == 200

    recent = client.get("/character/memory/recent")
    assert recent.status_code == 200
    payload = recent.json()
    assert payload["items"]

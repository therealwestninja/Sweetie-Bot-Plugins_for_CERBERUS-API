
from __future__ import annotations

from fastapi.testclient import TestClient

from sweetiebot.api.app import create_app


def test_first_real_slice_nudge_to_ack() -> None:
    app = create_app()
    client = TestClient(app)

    with client.websocket_connect("/ws/events") as ws:
        snapshot = ws.receive_json()
        assert snapshot["type"] == "events.snapshot"
        assert snapshot["replay_safe"] is False or snapshot["payload"].get("replay_safe") is True

        response = client.post("/character/nudge", json={"intent": "greet", "context": {"target": "guest"}})
        assert response.status_code == 200
        body = response.json()

        assert "reaction" in body
        assert "decision" in body
        assert body["reaction"]["emote"]
        assert body["decision"]["action_id"]

        reaction_event = ws.receive_json()
        assert reaction_event["type"] == "character.nudge_reaction"

        ack_event = ws.receive_json()
        assert ack_event["type"] == "cerberus.execution_ack"
        assert ack_event["payload"]["status"] == "ok"

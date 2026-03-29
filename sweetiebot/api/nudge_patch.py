
# IMPORT THESE INTO YOUR EXISTING app.py

import uuid
import asyncio
from fastapi import WebSocket
from sweetiebot.runtime.events import event_bus, make_event
from sweetiebot.runtime.execution import execute_action

def generate_reaction(intent: str):
    if intent == "greet":
        return {"speech": "Oh! Hello there~!", "emote": "happy", "attention": "user", "intensity": 0.8}
    if intent == "perk_up":
        return {"speech": "", "emote": "alert", "attention": "forward", "intensity": 0.6}
    return {"speech": "", "emote": "idle", "attention": "none", "intensity": 0.2}

def generate_decision(intent: str):
    return {
        "action_type": "emote",
        "action_id": intent,
        "parameters": {},
        "source_event_id": str(uuid.uuid4()),
        "safety_mode": "normal"
    }

def attach_nudge_and_ws(app, get_character_state, get_accessories, get_memory_summary):
    @app.post("/character/nudge")
    async def character_nudge(payload: dict):
        intent = payload.get("intent", "idle")
        reaction = generate_reaction(intent)
        decision = generate_decision(intent)

        await event_bus.emit(make_event(
            "character.nudge_reaction",
            {"reaction": reaction, "decision": decision},
            source="character"
        ))

        asyncio.create_task(execute_action(decision))
        return {"reaction": reaction, "decision": decision}

    @app.websocket("/ws/events")
    async def websocket_endpoint(ws: WebSocket):
        await event_bus.connect(ws)

        snapshot = make_event(
            "events.snapshot",
            {
                "character": get_character_state(),
                "accessories": get_accessories(),
                "memory": get_memory_summary()
            },
            replay_safe=True
        )
        await ws.send_json(snapshot)

        try:
            while True:
                await ws.receive_text()
        except Exception:
            event_bus.disconnect(ws)


import asyncio
from typing import Dict, Any

class EventBus:
    def __init__(self):
        self.connections = set()

    async def connect(self, websocket):
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket):
        self.connections.discard(websocket)

    async def emit(self, event: Dict[str, Any]):
        dead = []
        for ws in list(self.connections):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

event_bus = EventBus()

def make_event(event_type, payload, source="system", replay_safe=False):
    return {
        "type": event_type,
        "source": source,
        "schema_version": "1.0",
        "replay_safe": replay_safe,
        "payload": payload
    }

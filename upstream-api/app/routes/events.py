from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from upstream_api.app.main_support import get_runtime
from upstream_api.app.services.runtime import RuntimeState

router = APIRouter(tags=["events"])


@router.get("/events")
def get_events(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return {"items": runtime.recent_events()}


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    await websocket.accept()
    runtime = get_runtime()
    queue = runtime.subscribe_events()
    try:
        await websocket.send_json(
            {
                "type": "events.snapshot",
                "source": "sweetiebot_runtime",
                "payload": {
                    "items": runtime.recent_events(),
                    "character": runtime.get_character(),
                    "attention": runtime.get_attention(),
                    "routines": runtime.get_routines(),
                    "memory": runtime.get_memory_summary(),
                    "accessories": runtime.get_accessories(),
                    "plugins": runtime.get_plugins(),
                    "llm": runtime.get_llm_status(),
                },
            }
        )
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=15.0)
                await websocket.send_json(message)
            except TimeoutError:
                await websocket.send_json(
                    {
                        "type": "events.keepalive",
                        "source": "sweetiebot_runtime",
                        "payload": {"status": "idle"},
                    }
                )
    except WebSocketDisconnect:
        pass
    finally:
        runtime.unsubscribe_events(queue)

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from sweetiebot.runtime import SweetieBotRuntime


runtime = SweetieBotRuntime()
app = FastAPI(title="Sweetie Bot API")


class RememberRequest(BaseModel):
    kind: str
    content: str
    source: str = "api"
    scope: str = "session"


class CharacterStateUpdateRequest(BaseModel):
    mood: Optional[str] = None
    focus_target: Optional[str] = None
    active_routine: Optional[str] = None
    active_emote: Optional[str] = None
    accessory_scene: Optional[str] = None
    safe_mode: Optional[bool] = None
    degraded_mode: Optional[bool] = None
    last_input: Optional[str] = None
    last_reply: Optional[str] = None


class MoodEventRequest(BaseModel):
    event: str


class BehaviorSuggestRequest(BaseModel):
    user_text: Optional[str] = None


@app.get("/character/runtime-health")
def runtime_health():
    return runtime.runtime_health()


@app.get("/character/state")
def character_state():
    return runtime.character_state()


@app.post("/character/state")
def update_character_state(payload: CharacterStateUpdateRequest):
    return runtime.update_character_state(**payload.model_dump())


@app.get("/character/mood")
def mood_status():
    return runtime.mood_status()


@app.post("/character/mood/event")
def apply_mood_event(payload: MoodEventRequest):
    return runtime.apply_mood_event(payload.event)


@app.post("/character/mood/decay")
def decay_mood():
    return runtime.decay_mood()


@app.get("/character/behavior")
def behavior_status():
    return runtime.behavior_status()


@app.post("/character/behavior/suggest")
def suggest_behavior(payload: BehaviorSuggestRequest):
    return runtime.suggest_behavior(user_text=payload.user_text)


@app.post("/character/memory/remember")
def remember(payload: RememberRequest):
    return runtime.remember(
        kind=payload.kind,
        content=payload.content,
        source=payload.source,
        scope=payload.scope,
    )


@app.get("/character/memory/recent")
def recent_memory(limit: int = 10):
    return {"items": runtime.recall(limit=limit)}


@app.get("/character/memory/search")
def search_memory(text: str | None = None, kind: str | None = None, scope: str | None = None, limit: int = 10):
    return {"items": runtime.recall(text=text, kind=kind, scope=scope, limit=limit)}

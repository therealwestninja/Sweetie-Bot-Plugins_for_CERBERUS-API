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


class RoutineArbitrateRequest(BaseModel):
    requested_routine: Optional[str] = None


class AttentionSuggestRequest(BaseModel):
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


@app.get("/character/attention")
def attention_status():
    return runtime.attention_status()


@app.post("/character/attention/suggest")
def suggest_attention(payload: AttentionSuggestRequest):
    return runtime.suggest_attention(user_text=payload.user_text)


@app.post("/character/attention/apply")
def apply_attention(payload: AttentionSuggestRequest):
    return runtime.apply_attention(user_text=payload.user_text)


@app.get("/character/behavior")
def behavior_status():
    return runtime.behavior_status()


@app.post("/character/behavior/suggest")
def suggest_behavior(payload: BehaviorSuggestRequest):
    return runtime.suggest_behavior(user_text=payload.user_text)


@app.post("/character/behavior/arbitrate")
def arbitrate_behavior(payload: BehaviorSuggestRequest):
    return runtime.suggest_and_arbitrate_behavior(user_text=payload.user_text)


@app.get("/character/routines/arbitration")
def routine_arbitration_status():
    return runtime.routine_arbitrator.snapshot()


@app.post("/character/routines/arbitrate")
def arbitrate_routine(payload: RoutineArbitrateRequest):
    return runtime.arbitrate_routine(payload.requested_routine)


@app.get("/character/telemetry")
def telemetry_status():
    return runtime.telemetry_status()


@app.get("/character/telemetry/events")
def telemetry_events(limit: int = 25):
    return {"items": runtime.recent_trace_events(limit=limit)}


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

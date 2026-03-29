from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

from sweetiebot.persona.loader import PERSONA_LIBRARY
from sweetiebot.runtime import SweetieBotRuntime

app = FastAPI()
runtime = SweetieBotRuntime()

class SayReq(BaseModel):
    text: str

class PersonaReq(BaseModel):
    persona_id: str

class RoutineReq(BaseModel):
    routine_id: str

@app.get("/")
def root():
    return {"status": "scaffold-online", "character": runtime.character_state()}

@app.post("/character/say")
def say(req: SayReq):
    structured = runtime.handle_text(req.text)
    return {
        "intent": structured["reply"]["intent"],
        "reply": structured["reply"]["text"],
        "emote_id": structured["reply"]["directive"]["emote_id"],
        "provider": "local",
        "audio": {"sink": "disabled"},
    }

@app.get("/character/personas")
def personas():
    return {"items": [{"id": key} for key in PERSONA_LIBRARY]}

@app.post("/character/persona")
def persona(req: PersonaReq):
    runtime.configure_persona(PERSONA_LIBRARY[req.persona_id])
    return {"character": runtime.character_state()}

@app.get("/character/llm")
def llm():
    return {"provider": "local", "audio": {"sink": "disabled"}}

@app.post("/character/routine")
def routine(req: RoutineReq):
    runtime.state.current_routine_id = req.routine_id
    return {"active": req.routine_id, "step_count": 3}

@app.post("/character/cancel")
def cancel():
    runtime.state.current_routine_id = None
    return {"active_routine": None}

@app.get("/events")
def events():
    return {"items": runtime.recent_trace_events(limit=10)}

@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    await ws.send_json({"type": "events.snapshot", "payload": {"character": runtime.character_state(), "llm": {"provider": "local"}}})
    await ws.send_json({"type": "persona.selected", "payload": {"character": {"persona_id": "sweetiebot_companion"}}})
    await ws.close()

@app.get("/character/foundation")
def foundation():
    return {
        "profile": {"id": runtime.state.persona_id},
        "available_emotes": [{"id": "curious_headtilt"}, {"id": "happy_bounce"}],
        "available_routines": [{"id": "greeting_01"}, {"id": "photo_pose"}],
        "available_accessory_scenes": [{"id": "eyes_curious"}, {"id": "eyes_happy"}],
    }

@app.post("/character/emote")
def emote(payload: dict):
    emote_id = payload["emote_id"]
    scene_id = "eyes_curious" if emote_id == "curious_headtilt" else "eyes_happy"
    return {"emote_id": emote_id, "accessory_scene": {"scene_id": scene_id}, "character": {"active_accessory_scene": scene_id}}

@app.get("/routines/{routine_id}/plan")
def routine_plan(routine_id: str):
    return {"routine_id": routine_id, "step_count": 3, "estimated_duration_ms": 3200, "steps": [{"step_index": 1}, {"step_index": 2}, {"step_index": 3}]}

@app.post("/accessories/scene")
def accessories_scene(payload: dict):
    return {"scene_id": payload["scene_id"]}

@app.get("/accessories/scenes")
def accessories_scenes():
    return {"items": [{"id": "eyes_happy"}, {"id": "eyes_curious"}]}

@app.get("/plugins")
def plugins():
    return {"items": [{"name": "sweetiebot_persona"}, {"name": "sweetiebot_dialogue"}, {"name": "sweetiebot_routines"}, {"name": "sweetiebot_accessories"}]}

@app.get("/routines")
def routines():
    return {"items": [{"id": "greeting_01", "title": "Greeting 01", "steps": [{"type": "focus"}, {"type": "speak"}, {"type": "emote"}]}]}

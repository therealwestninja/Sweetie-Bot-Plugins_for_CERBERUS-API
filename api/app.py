from __future__ import annotations

import time
from typing import Any, Callable

from fastapi import FastAPI, WebSocket
from pydantic import BaseModel, Field

from sweetiebot.integration.cerberus_mapper import CerberusMapper
from sweetiebot.integration.schemas import (
    CharacterResponse,
    MoodLabel,
    SafetyMode,
    WSEvent,
    WSEventType,
)
from sweetiebot.memory.context import build_context_summary, extract_recent_commands
from sweetiebot.observability.structured_log import get_ledger, get_logger
from sweetiebot.persona.loader import PERSONA_LIBRARY
from sweetiebot.runtime import SweetieBotRuntime
from sweetiebot.safety.gate import SafetyGate

_log = get_logger("api")


class SpeakRequest(BaseModel):
    text: str
    voice: str | None = None


class SayRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class PluginConfigRequest(BaseModel):
    plugins: dict[str, dict[str, Any]]


class PersonaPayloadRequest(BaseModel):
    payload: dict[str, Any]


class PersonaSelectRequest(BaseModel):
    persona_id: str


class StateRequest(BaseModel):
    mood: str | None = None
    focus_target: str | None = None


class AttentionRequest(BaseModel):
    user_text: str | None = None


class MemoryRequest(BaseModel):
    kind: str
    content: str
    source: str = "api"
    scope: str = "session"


class RoutineRequest(BaseModel):
    requested_routine: str | None = None
    routine_id: str | None = None


class EmoteRequest(BaseModel):
    dialogue_intent: str | None = None


def _runtime_health(runtime: SweetieBotRuntime) -> dict[str, Any]:
    if hasattr(runtime.plugins, "health_summary"):
        plugins = runtime.plugins.health_summary()
    else:
        from sweetiebot.plugins.health import summarize_plugin_health
        plugins = summarize_plugin_health(runtime.plugins.plugins()) if hasattr(runtime.plugins, "plugins") else {"counts": {"total": 0}}
    return {"runtime_ok": True, "plugins": plugins}


def create_app(runtime_factory: Callable[[], SweetieBotRuntime] | None = None) -> FastAPI:
    factory = runtime_factory or SweetieBotRuntime
    app = FastAPI(title="Sweetie-Bot API", version="0.1.1")
    runtime = factory()
    app.state.runtime = runtime

    # ── Integration layer ──────────────────────────────────────────────────
    mapper = CerberusMapper(dry_run=False)
    gate = SafetyGate()
    app.state.mapper = mapper
    app.state.gate = gate

    # Register integration + debug routes
    from sweetiebot.api.routes.integration import create_integration_router
    integration_router, debug_router = create_integration_router(mapper, gate)
    app.include_router(integration_router)
    app.include_router(debug_router)

    ledger = get_ledger()

    @app.get("/")
    def root() -> dict[str, Any]:
        return {"status": "scaffold-online", "character": runtime.character_state()}

    @app.get("/health")
    @app.get("/character/health")
    def health() -> dict[str, Any]:
        return _runtime_health(runtime)

    @app.post("/speak")
    def speak(payload: SpeakRequest):
        result = runtime.speak(payload.text).to_dict()
        if payload.voice:
            result.setdefault("speech", {})["voice"] = payload.voice
            result.setdefault("speech", {})["voice_profile"] = payload.voice
        return result

    @app.post("/character/speak-test")
    def speak_test(payload: SpeakRequest):
        result = runtime.speak(payload.text).to_dict()
        speech = dict(result.get("speech", {}))
        playback = dict(result.get("playback", {}))
        if payload.voice:
            speech["voice"] = payload.voice
            speech["voice_profile"] = payload.voice
        flat = {**speech, **playback, "voice": payload.voice or speech.get("voice") or speech.get("voice_profile") or "default"}
        return flat

    @app.get("/character/foundation")
    def foundation() -> dict[str, Any]:
        return {
            "persona_id": runtime.state.persona_id,
            "dialogue_style": runtime.persona_payload["dialogue_style"],
            "defaults": runtime.persona_payload["defaults"],
            "state": runtime.state.to_dict(),
            "profile": {"id": runtime.state.persona_id},
            "available_emotes": [
                {"id": "curious_headtilt"},
                {"id": "warm_smile"},
            ],
            "available_routines": [
                {"id": "greeting_01"},
                {"id": "greet_guest"},
            ],
            "available_accessory_scenes": [
                {"id": "eyes_curious"},
                {"id": "eyes_happy"},
            ],
        }

    @app.get("/character/plugins")
    @app.get("/plugins")
    def plugins() -> dict[str, Any]:
        plugin_items = runtime.plugin_summary()
        return {"plugins": plugin_items, "items": [{"name": n} for n in ["sweetiebot_persona", "sweetiebot_dialogue", "sweetiebot_routines", "sweetiebot_accessories"]]}

    @app.post("/character/plugins/configure")
    def configure_plugins(request: PluginConfigRequest) -> dict[str, Any]:
        configured = runtime.configure_plugins(request.plugins)
        return {"ok": True, "configured": configured, "plugins": runtime.plugin_summary()}

    @app.post("/character/persona")
    def set_persona(request: PersonaPayloadRequest | PersonaSelectRequest) -> dict[str, Any]:
        if hasattr(request, "payload"):
            state = runtime.configure_persona(request.payload)
        else:
            state = runtime.configure_persona(PERSONA_LIBRARY[request.persona_id])
        return {"ok": True, "state": state.to_dict(), "character": runtime.character_state()}

    @app.get("/character/personas")
    def personas() -> dict[str, Any]:
        return {"items": [{"id": key} for key in PERSONA_LIBRARY]}

    @app.post("/character/say")
    def say(request: SayRequest) -> dict[str, Any]:
        # ── Memory context feedback loop ───────────────────────────────
        recent_memories = runtime.recall(limit=12)
        state = runtime.character_state()
        context_summary = build_context_summary(
            recent_memories,
            current_mood=state.get("mood", "calm"),
            current_routine=state.get("active_routine"),
        )
        recent_commands = extract_recent_commands(recent_memories)

        result = runtime.handle_text(request.text) if hasattr(runtime, "handle_text") else {}
        legacy = runtime.say(request.text).to_dict() if hasattr(runtime, "say") else {}
        response = {**legacy, **result}
        emote_id = result.get("reply", {}).get("directive", {}).get("emote_id") if result else None
        if emote_id:
            response["emote_id"] = emote_id

        # Attach context summary and recent-command hints to response metadata
        response["_context"] = {
            "memory_summary": context_summary,
            "recent_routines": recent_commands["routines"],
            "recent_emotes": recent_commands["emotes"],
        }

        # Record to ledger
        ledger.record("character.say", {
            "user_text": request.text,
            "emote_id": emote_id,
            "mood": state.get("mood"),
            "context_summary_len": len(context_summary),
        })

        _log.decision("character.say processed", context={
            "text_len": len(request.text),
            "mood": state.get("mood"),
            "recent_routines": recent_commands["routines"][:2],
        })

        return response

    @app.post("/character/stop")
    @app.post("/character/cancel")
    def stop() -> dict[str, Any]:
        state = runtime.apply_operator_stop()
        return {"ok": True, "state": state.to_dict(), "active_routine": None}

    @app.post("/character/reset-neutral")
    def reset_neutral() -> dict[str, Any]:
        state = runtime.reset_neutral()
        return {"ok": True, "state": state.to_dict()}

    @app.get("/character/state")
    def get_state() -> dict[str, Any]:
        return runtime.character_state()

    @app.post("/character/state")
    def update_state(payload: StateRequest) -> dict[str, Any]:
        return runtime.update_character_state(mood=payload.mood, focus_target=payload.focus_target)

    @app.get("/character/mood")
    def mood() -> dict[str, Any]:
        return {"current_mood": runtime.character_state()["mood"]}

    @app.post("/character/mood/event")
    def mood_event(payload: dict[str, str]) -> dict[str, Any]:
        return runtime.apply_mood_event(payload["event"])

    @app.post("/character/mood/decay")
    def mood_decay() -> dict[str, Any]:
        new_mood = runtime.mood_engine.decay(runtime.character_state()["mood"])
        runtime.update_character_state(mood=new_mood)
        return {"mood": new_mood}

    @app.get("/character/attention")
    def attention() -> dict[str, Any]:
        return {"current_focus": runtime.character_state().get("focus_target")}

    @app.post("/character/attention/suggest")
    def attention_suggest(request: AttentionRequest) -> dict[str, Any]:
        return runtime.apply_attention(request.user_text or "")["suggestion"]

    @app.post("/character/attention/apply")
    def attention_apply(request: AttentionRequest) -> dict[str, Any]:
        return runtime.apply_attention(request.user_text or "")

    @app.get("/character/behavior")
    def behavior() -> dict[str, Any]:
        return {"director": runtime.behavior_director.snapshot()}

    @app.post("/character/behavior/suggest")
    def behavior_suggest(request: AttentionRequest) -> dict[str, Any]:
        return runtime.suggest_behavior(request.user_text or "")

    @app.get("/character/perception")
    def perception() -> dict[str, Any]:
        return {"sources": [p.plugin_id for p in runtime.plugins.get_perception_sources()]}

    @app.post("/character/perception/poll")
    def perception_poll() -> dict[str, Any]:
        return {"items": runtime.poll_perception()}

    @app.post("/character/perception/apply")
    def perception_apply() -> dict[str, Any]:
        return runtime.apply_perception()

    @app.post("/character/memory/remember")
    def remember(request: MemoryRequest) -> dict[str, Any]:
        from sweetiebot.memory.models import MemoryRecord
        record = runtime.memory_store.put(MemoryRecord(kind=request.kind, content=request.content, source=request.source, scope=request.scope))
        return record.to_dict()

    @app.get("/character/memory/recent")
    def memory_recent() -> dict[str, Any]:
        return {"items": runtime.recall(limit=10)}

    @app.get("/character/emotes")
    def emotes() -> dict[str, Any]:
        return {"mapper": "rule_based"}

    @app.post("/character/emotes/map")
    def emote_map(request: EmoteRequest) -> dict[str, Any]:
        return runtime.emote_mapper.map_emote(current_mood=runtime.character_state()["mood"], dialogue_intent=request.dialogue_intent).to_dict()


    @app.get("/character/dialogue")
    def dialogue_status() -> dict[str, Any]:
        return runtime.dialogue_status()

    @app.post("/character/dialogue/generate")
    def dialogue_generate(payload: dict[str, str]) -> dict[str, Any]:
        return runtime.generate_dialogue(payload.get("user_text", ""))

    @app.get("/character/telemetry")
    def telemetry() -> dict[str, Any]:
        return {"sink": "inmemory", "recent_events": runtime.recent_trace_events(limit=10)}

    @app.get("/character/telemetry/events")
    def telemetry_events(limit: int = 5) -> dict[str, Any]:
        return {"items": runtime.recent_trace_events(limit=limit)}
    @app.get("/character/routines/arbitration")
    def routine_arbitration() -> dict[str, Any]:
        return runtime.arbitrator.snapshot()

    @app.post("/character/routines/arbitrate")
    def routine_arbitrate(request: RoutineRequest) -> dict[str, Any]:
        requested = request.requested_routine or request.routine_id
        return runtime.arbitrator.arbitrate(requested_routine=requested, active_routine=runtime.state.current_routine_id)

    @app.get("/routines")
    def routines() -> dict[str, Any]:
        return {"items": [{"id": "greeting_01", "title": "Greeting 01", "steps": [{"type": "focus"}]}]}

    @app.get("/routines/{routine_id}/plan")
    def routine_plan(routine_id: str) -> dict[str, Any]:
        return {"routine_id": routine_id, "step_count": 3, "estimated_duration_ms": 3200, "steps": [{"step_index": 1}, {"step_index": 2}, {"step_index": 3}]}

    @app.post("/character/routine")
    def activate_routine(request: RoutineRequest) -> dict[str, Any]:
        routine_id = request.routine_id or request.requested_routine or "greeting_01"
        runtime.state.current_routine_id = routine_id
        return {"active": routine_id, "step_count": 3}

    @app.post("/character/emote")
    def emote(payload: dict[str, str]) -> dict[str, Any]:
        emote_id = payload["emote_id"]
        scene = "eyes_curious" if emote_id == "curious_headtilt" else "eyes_happy"
        runtime.state.current_emote_id = emote_id
        runtime.state.current_accessory_scene_id = scene
        return {"emote_id": emote_id, "accessory_scene": {"scene_id": scene}, "character": {"active_accessory_scene": scene}}

    @app.get("/accessories/scenes")
    def accessory_scenes() -> dict[str, Any]:
        return {"items": [{"id": "eyes_happy"}, {"id": "eyes_curious"}]}

    @app.post("/accessories/scene")
    def accessory_scene(payload: dict[str, str]) -> dict[str, Any]:
        runtime.state.current_accessory_scene_id = payload["scene_id"]
        return {"scene_id": payload["scene_id"]}

    @app.get("/character/llm")
    def llm() -> dict[str, Any]:
        return {"provider": "local", "audio": {"sink": "disabled"}}

    @app.get("/events")
    def events() -> dict[str, Any]:
        return {"items": runtime.recent_trace_events(limit=20)}

    @app.websocket("/ws/events")
    async def websocket_events(ws: WebSocket) -> None:
        await ws.accept()

        char_state = runtime.character_state()
        safety_mode = gate.safety_mode.value

        # ── Snapshot event (replay-safe: carries full state) ───────────
        snapshot_evt = WSEvent(
            event_type=WSEventType.EVENTS_SNAPSHOT,
            replay_safe=True,
            payload={
                "character": char_state,
                "safety_mode": safety_mode,
                "gate": gate.snapshot(),
                "mapper": mapper.snapshot(),
                "llm": {"provider": "local"},
                "recent_decisions": ledger.recent(limit=5),
            },
        )
        await ws.send_json(snapshot_evt.model_dump())

        # ── Persona selected event ─────────────────────────────────────
        persona_evt = WSEvent(
            event_type=WSEventType.PERSONA_SELECTED,
            replay_safe=True,
            payload={"character": char_state},
        )
        await ws.send_json(persona_evt.model_dump())

        # ── Character state update ─────────────────────────────────────
        state_evt = WSEvent(
            event_type=WSEventType.CHARACTER_STATE_UPDATED,
            replay_safe=True,
            payload={"character": char_state, "safety_mode": safety_mode},
        )
        await ws.send_json(state_evt.model_dump())

        await ws.close()

    @app.post("/character/respond")
    def character_respond(request: SayRequest) -> dict[str, Any]:
        """
        Primary endpoint consumed by CERBERUS.
        Returns a fully typed CharacterResponse (schema_version=1.0).
        """
        state = runtime.character_state()
        dialogue = runtime.generate_dialogue(request.text)
        emote = runtime.map_emote(
            dialogue_intent=dialogue.get("intent"),
            suggested_emote_id=dialogue.get("emote_id"),
        )
        behavior = runtime.suggest_behavior(request.text)

        # Map mood string to MoodLabel (default calm if unrecognised)
        mood_str = state.get("mood", "calm")
        try:
            mood = MoodLabel(mood_str)
        except ValueError:
            mood = MoodLabel.CALM

        char_response = CharacterResponse(
            reply_text=dialogue.get("spoken_text"),
            emote_id=emote.get("emote_id"),
            routine_id=behavior.get("routine_id"),
            safe_mode=state.get("safe_mode", False),
            degraded_mode=state.get("degraded_mode", False),
            mood=mood,
            intent=dialogue.get("intent"),
            source="sweetiebot",
            metadata={
                "dialogue_confidence": dialogue.get("confidence"),
                "behavior_action": behavior.get("action"),
                "behavior_priority": behavior.get("priority"),
            },
        )

        ledger.record("character.respond", {
            "response_id": char_response.response_id,
            "routine_id": char_response.routine_id,
            "emote_id": char_response.emote_id,
            "mood": char_response.mood.value,
            "intent": char_response.intent,
        })

        return char_response.model_dump()

    return app


app = create_app()

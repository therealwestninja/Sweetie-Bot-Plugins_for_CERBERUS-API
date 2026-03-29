from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime
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
from sweetiebot.integration.first_slice import (
    adapt_nudge_response,
    make_snapshot_payload,
    publish_canonical_nudge_event,
    run_cerberus_stub,
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


class NudgeRequest(BaseModel):
    nudge_type: str = "attention"
    intent: str | None = None
    source: str = "companion_web"
    note: str = ""
    context: dict[str, Any] = Field(default_factory=dict)


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


@dataclass(slots=True)
class EventEnvelope:
    event_type: str
    source: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.event_type,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "source": self.source,
            "payload": self.payload,
        }


class EventHub:
    def __init__(self) -> None:
        self._listeners: set[asyncio.Queue[dict[str, Any]]] = set()

    def connect(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._listeners.add(queue)
        return queue

    def disconnect(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._listeners.discard(queue)

    async def publish(self, envelope: EventEnvelope) -> None:
        payload = envelope.to_dict()
        for queue in list(self._listeners):
            await queue.put(payload)


class IntegrationBridge:
    def __init__(self, runtime: SweetieBotRuntime, events: EventHub) -> None:
        self.runtime = runtime
        self.events = events

    def foundation(self) -> dict[str, Any]:
        character = self.runtime.character_state()
        return {
            "persona_id": self.runtime.state.persona_id,
            "dialogue_style": self.runtime.persona_payload["dialogue_style"],
            "defaults": self.runtime.persona_payload["defaults"],
            "state": self.runtime.state.to_dict(),
            "profile": {"id": self.runtime.state.persona_id},
            "available_emotes": [
                {"id": "curious_headtilt"},
                {"id": "warm_smile"},
                {"id": "happy_bounce"},
            ],
            "available_routines": [
                {"id": "greeting_01"},
                {"id": "greet_guest"},
                {"id": "return_to_neutral"},
            ],
            "available_accessory_scenes": [
                {"id": "eyes_curious"},
                {"id": "eyes_happy"},
                {"id": "eyes_neutral"},
            ],
            "character": character,
        }

    def character_payload(self) -> dict[str, Any]:
        state = self.runtime.character_state()
        return {
            **state,
            "active_accessory_scene": state.get("accessory_scene"),
            "available_personas": list(PERSONA_LIBRARY.keys()),
        }

    def memory_summary(self) -> dict[str, Any]:
        items = self.runtime.recall(limit=50)
        known_people = sorted(
            {entry["content"] for entry in items if entry.get("kind") == "observation" and entry.get("content")}
        )
        preferences = sorted(
            {entry["content"] for entry in items if entry.get("kind") in {"preference", "operator_preference"}}
        )
        return {
            "known_people": known_people,
            "preferences": preferences,
            "recent": items[:10],
            "count": len(items),
        }

    def accessories_payload(self) -> dict[str, Any]:
        character = self.runtime.character_state()
        active_scene = character.get("accessory_scene")
        return {
            "active_scene": active_scene,
            "audio": {"sink": self.audio_sink()},
            "capabilities": {
                "scene_switching": True,
                "onboard_audio": self.audio_sink() != "disabled",
            },
            "items": [
                {"id": "eyes_happy", "kind": "scene", "active": active_scene == "eyes_happy"},
                {"id": "eyes_curious", "kind": "scene", "active": active_scene == "eyes_curious"},
                {"id": "eyes_neutral", "kind": "scene", "active": active_scene == "eyes_neutral"},
            ],
        }

    def llm_payload(self) -> dict[str, Any]:
        return {"provider": "local", "audio": {"sink": self.audio_sink()}}

    def audio_sink(self) -> str:
        playback = self.runtime.state.get("last_playback") or {}
        if not playback.get("ok"):
            return "disabled"
        sink = str(playback.get("output") or playback.get("sink") or "cerberus_go2_onboard_audio")
        if sink == "sweetiebot.mock_audio_output":
            return "cerberus_go2_onboard_audio"
        return sink

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "character": self.character_payload(),
            "accessories": self.accessories_payload(),
            "memory": self.memory_summary(),
            "plugins": {"items": self.runtime.plugin_summary()},
            "llm": self.llm_payload(),
        }

    async def publish(self, event_type: str, *, source: str, payload: dict[str, Any]) -> None:
        await self.events.publish(EventEnvelope(event_type=event_type, source=source, payload=payload))


async def _publish_refresh(bridge: IntegrationBridge, event_type: str, source: str, extra_payload: dict[str, Any] | None = None) -> None:
    payload = bridge.snapshot_payload()
    if extra_payload:
        payload.update(extra_payload)
    await bridge.publish(event_type, source=source, payload=payload)


def _runtime_health(runtime: SweetieBotRuntime) -> dict[str, Any]:
    if hasattr(runtime.plugins, "health_summary"):
        plugins = runtime.plugins.health_summary()
    else:
        from sweetiebot.plugins.health import summarize_plugin_health
        plugins = summarize_plugin_health(runtime.plugins.plugins()) if hasattr(runtime.plugins, "plugins") else {"counts": {"total": 0}}
    return {"runtime_ok": True, "plugins": plugins}


def create_app(
    runtime_factory: Callable[[], SweetieBotRuntime] | None = None,
    *,
    legacy_say_response: bool = False,
) -> FastAPI:
    factory = runtime_factory or SweetieBotRuntime
    app = FastAPI(title="Sweetie-Bot", version="0.1.1")
    runtime = factory()
    events = EventHub()
    bridge = IntegrationBridge(runtime=runtime, events=events)
    app.state.runtime = runtime
    app.state.event_hub = events
    app.state.integration_bridge = bridge

    # ── Integration layer (resolved from plugin registry) ─────────────
    # The registry already has AllowlistCerberusMapperPlugin and
    # RuleBasedSafetyGatePlugin registered via register_builtins().
    # Operators can override these by registering a higher-priority plugin
    # of type CERBERUS_MAPPER or SAFETY_GATE before create_app() is called.
    # Defensive getattr() allows test stubs (FakeRegistry) to work without
    # implementing the new accessor methods.
    _get_mapper  = getattr(runtime.plugins, "get_cerberus_mapper", lambda: None)
    _get_gate    = getattr(runtime.plugins, "get_safety_gate",     lambda: None)
    _get_ctx     = getattr(runtime.plugins, "get_memory_context",  lambda: None)
    _mapper_plugin = _get_mapper()
    _gate_plugin   = _get_gate()
    _ctx_plugin    = _get_ctx()

    # Unwrap to the underlying CerberusMapper / SafetyGate instances so
    # the existing integration routes work with their native APIs.
    mapper: CerberusMapper = (
        _mapper_plugin._mapper
        if _mapper_plugin and hasattr(_mapper_plugin, "_mapper")
        else CerberusMapper(dry_run=False)
    )
    gate: SafetyGate = (
        _gate_plugin._gate
        if _gate_plugin and hasattr(_gate_plugin, "_gate")
        else SafetyGate()
    )
    ledger = get_ledger()
    app.state.mapper        = mapper
    app.state.gate          = gate
    app.state.ledger        = ledger
    app.state.mapper_plugin = _mapper_plugin
    app.state.gate_plugin   = _gate_plugin
    app.state.ctx_plugin    = _ctx_plugin

    # Connect safety gate to event pipeline for automatic escalation
    runtime.set_safety_gate(gate)

    from sweetiebot.api.routes.integration import create_integration_router
    integration_router, debug_router = create_integration_router(mapper, gate)
    app.include_router(integration_router)
    app.include_router(debug_router)

    # ── Nudge handler (Companion Web Interface → gentle suggestions) ───
    from sweetiebot.behavior.nudge_handler import NudgeHandler
    nudge_handler = NudgeHandler()
    app.state.nudge_handler = nudge_handler

    @app.get("/")
    def root() -> dict[str, Any]:
        return {"status": "scaffold-online", "character": runtime.character_state()}

    @app.get("/character")
    def character() -> dict[str, Any]:
        return bridge.character_payload()

    @app.get("/health")
    @app.get("/character/health")
    def health() -> dict[str, Any]:
        return _runtime_health(runtime)

    @app.post("/speak")
    async def speak(payload: SpeakRequest):
        result = runtime.speak(payload.text).to_dict()
        if payload.voice:
            result.setdefault("speech", {})["voice"] = payload.voice
            result.setdefault("speech", {})["voice_profile"] = payload.voice
        await _publish_refresh(bridge, "dialogue.reply_ready", "sweetiebot_dialogue", {"speech": result.get("speech")})
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
        return bridge.foundation()

    @app.get("/character/plugins")
    @app.get("/plugins")
    def plugins() -> dict[str, Any]:
        plugin_items = runtime.plugin_summary()
        return {
            "plugins": plugin_items,
            "items": [{"name": n} for n in ["sweetiebot_persona", "sweetiebot_dialogue", "sweetiebot_routines", "sweetiebot_accessories"]],
        }

    @app.post("/character/plugins/configure")
    async def configure_plugins(request: PluginConfigRequest) -> dict[str, Any]:
        configured = runtime.configure_plugins(request.plugins)
        await _publish_refresh(bridge, "plugins.configured", "sweetiebot_plugins", {"configured": configured})
        return {"ok": True, "configured": configured, "plugins": runtime.plugin_summary()}

    @app.post("/character/persona")
    async def set_persona(request: PersonaPayloadRequest | PersonaSelectRequest) -> dict[str, Any]:
        if hasattr(request, "payload"):
            state = runtime.configure_persona(request.payload)
        else:
            state = runtime.configure_persona(PERSONA_LIBRARY[request.persona_id])
        await _publish_refresh(bridge, "persona.selected", "sweetiebot_persona")
        return {"ok": True, "state": state.to_dict(), "character": runtime.character_state()}

    @app.get("/character/personas")
    def personas() -> dict[str, Any]:
        return {"items": [{"id": key, "display_name": PERSONA_LIBRARY[key].get("name", key), "motion_style": PERSONA_LIBRARY[key].get("motion_style", {})} for key in PERSONA_LIBRARY]}

    @app.post("/character/say")
    async def say(request: SayRequest) -> dict[str, Any]:
        t0 = time.perf_counter()

        # ── Memory context feedback loop ───────────────────────────────
        # Use the MemoryContextPlugin from the registry if available,
        # falling back to the bare module functions.
        recent_memories = runtime.recall(limit=12)
        state = runtime.character_state()
        if _ctx_plugin is not None:
            context_summary = _ctx_plugin.build_context_summary(
                recent_memories,
                current_mood=state.get("mood", "calm"),
                current_routine=state.get("active_routine"),
            )
            recent_commands = _ctx_plugin.extract_recent_commands(recent_memories)
        else:
            context_summary = build_context_summary(
                recent_memories,
                current_mood=state.get("mood", "calm"),
                current_routine=state.get("active_routine"),
            )
            recent_commands = extract_recent_commands(recent_memories)

        result = runtime.handle_text(request.text)
        legacy = runtime.say(request.text).to_dict()
        response = {**legacy, **result}
        response["audio"] = {"sink": bridge.audio_sink()}
        emote_id = result.get("reply", {}).get("directive", {}).get("emote_id")
        response["emote_id"] = emote_id
        if legacy_say_response:
            response["reply_structured"] = result["reply"]
            response["reply"] = result["reply"]["text"]

        # Attach context hints so the Web UI / CERBERUS can see session state
        response["_context"] = {
            "memory_summary": context_summary,
            "recent_routines": recent_commands["routines"],
            "recent_emotes": recent_commands["emotes"],
        }

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        ledger.record("character.say", {
            "user_text": request.text,
            "emote_id": emote_id,
            "mood": state.get("mood"),
            "context_summary_len": len(context_summary),
            "recent_routines": recent_commands["routines"][:2],
        }, elapsed_ms=elapsed_ms)

        _log.decision("character.say", context={
            "text_len": len(request.text),
            "mood": state.get("mood"),
            "emote": emote_id,
            "elapsed_ms": elapsed_ms,
        })

        await _publish_refresh(
            bridge,
            "dialogue.reply_ready",
            "sweetiebot_dialogue",
            {"reply": result["reply"], "character": bridge.character_payload()},
        )
        return response

    @app.post("/character/stop")
    @app.post("/character/cancel")
    async def stop() -> dict[str, Any]:
        state = runtime.apply_operator_stop()
        runtime.state.current_routine_id = None
        await _publish_refresh(bridge, "routine.completed", "sweetiebot_routines", {"active_routine": None})
        return {"ok": True, "state": state.to_dict(), "active_routine": None}

    @app.post("/character/reset-neutral")
    async def reset_neutral() -> dict[str, Any]:
        state = runtime.reset_neutral()
        await _publish_refresh(bridge, "persona.changed", "sweetiebot_emotes")
        return {"ok": True, "state": state.to_dict()}

    @app.get("/character/state")
    def get_state() -> dict[str, Any]:
        return runtime.character_state()

    @app.post("/character/state")
    async def update_state(payload: StateRequest) -> dict[str, Any]:
        updated = runtime.update_character_state(mood=payload.mood, focus_target=payload.focus_target)
        await _publish_refresh(bridge, "persona.changed", "sweetiebot_state")
        return updated

    @app.get("/character/mood")
    def mood() -> dict[str, Any]:
        return {"current_mood": runtime.character_state()["mood"]}

    @app.post("/character/mood/event")
    async def mood_event(payload: dict[str, str]) -> dict[str, Any]:
        updated = runtime.apply_mood_event(payload["event"])
        await _publish_refresh(bridge, "persona.changed", "sweetiebot_mood", updated)
        return updated

    @app.post("/character/mood/decay")
    async def mood_decay() -> dict[str, Any]:
        new_mood = runtime.mood_engine.decay(runtime.character_state()["mood"])
        runtime.update_character_state(mood=new_mood)
        await _publish_refresh(bridge, "persona.changed", "sweetiebot_mood", {"mood": new_mood})
        return {"mood": new_mood}

    @app.get("/character/attention")
    def attention() -> dict[str, Any]:
        return {"current_focus": runtime.character_state().get("focus_target")}

    @app.post("/character/attention/suggest")
    def attention_suggest(request: AttentionRequest) -> dict[str, Any]:
        return runtime.apply_attention(request.user_text or "")["suggestion"]

    @app.post("/character/attention/apply")
    async def attention_apply(request: AttentionRequest) -> dict[str, Any]:
        result = runtime.apply_attention(request.user_text or "")
        await _publish_refresh(bridge, "attention.target_changed", "sweetiebot_attention", result)
        return result

    @app.post("/character/focus")
    async def character_focus(request: AttentionRequest) -> dict[str, Any]:
        result = runtime.apply_attention(request.user_text or "")
        await _publish_refresh(bridge, "attention.target_changed", "sweetiebot_attention", result)
        return result

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
    async def perception_apply() -> dict[str, Any]:
        result = runtime.apply_perception()
        await _publish_refresh(bridge, "attention.target_changed", "sweetiebot_perception", result)
        return result

    @app.post("/character/memory/remember")
    async def remember(request: MemoryRequest) -> dict[str, Any]:
        from sweetiebot.memory.models import MemoryRecord
        record = runtime.memory_store.put(MemoryRecord(kind=request.kind, content=request.content, source=request.source, scope=request.scope))
        await _publish_refresh(bridge, "memory.updated", "sweetiebot_memory", {"record": record.to_dict()})
        return record.to_dict()

    @app.get("/character/memory/recent")
    def memory_recent() -> dict[str, Any]:
        return {"items": runtime.recall(limit=10)}

    @app.get("/memory/summary")
    def memory_summary() -> dict[str, Any]:
        return bridge.memory_summary()

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
        items_by_id: dict[str, dict[str, Any]] = {}
        for routine_id in runtime.routines.list_ids():
            plan = runtime.routines.get(routine_id) or {"steps": []}
            items_by_id[routine_id] = {"id": routine_id, "title": plan.get("title", routine_id.replace("_", " ").title()), "steps": plan.get("steps", [])}
        items_by_id.setdefault("greeting_01", {"id": "greeting_01", "title": "Greeting 01", "steps": [{"type": "focus"}, {"type": "say"}, {"type": "emote"}]})
        return {"items": list(items_by_id.values())}

    @app.get("/routines/{routine_id}/plan")
    def routine_plan(routine_id: str) -> dict[str, Any]:
        plan = runtime.routines.get(routine_id) or {}
        steps = plan.get("steps", [{"step_index": 1}, {"step_index": 2}, {"step_index": 3}])
        normalized_steps = [{"step_index": index + 1, **step} for index, step in enumerate(steps)]
        return {
            "routine_id": routine_id,
            "step_count": len(normalized_steps),
            "estimated_duration_ms": max(1200, len(normalized_steps) * 1000),
            "steps": normalized_steps,
        }

    @app.post("/character/routine")
    async def activate_routine(request: RoutineRequest) -> dict[str, Any]:
        routine_id = request.routine_id or request.requested_routine or "greeting_01"
        runtime.state.current_routine_id = routine_id
        await _publish_refresh(bridge, "routine.started", "sweetiebot_routines", {"active_routine": routine_id})
        plan = runtime.routines.get(routine_id) or {"steps": [{"type": "focus"}, {"type": "say"}, {"type": "emote"}]}
        return {"active": routine_id, "step_count": len(plan.get("steps", [])) or 3}

    @app.post("/character/emote")
    async def emote(payload: dict[str, str]) -> dict[str, Any]:
        emote_id = payload["emote_id"]
        scene = "eyes_curious" if emote_id == "curious_headtilt" else "eyes_happy"
        runtime.state.current_emote_id = emote_id
        runtime.state.current_accessory_scene_id = scene
        response = {"emote_id": emote_id, "accessory_scene": {"scene_id": scene}, "character": {"active_accessory_scene": scene}}
        await _publish_refresh(bridge, "persona.changed", "sweetiebot_emotes", response)
        return response

    @app.get("/accessories")
    def accessories() -> dict[str, Any]:
        return bridge.accessories_payload()

    @app.get("/accessories/scenes")
    def accessory_scenes() -> dict[str, Any]:
        return {"items": [{"id": "eyes_happy"}, {"id": "eyes_curious"}, {"id": "eyes_neutral"}]}

    @app.post("/accessories/scene")
    async def accessory_scene(payload: dict[str, str]) -> dict[str, Any]:
        runtime.state.current_accessory_scene_id = payload["scene_id"]
        result = {"scene_id": payload["scene_id"]}
        await _publish_refresh(bridge, "persona.changed", "sweetiebot_accessories", result)
        return result

    @app.get("/character/llm")
    def llm() -> dict[str, Any]:
        return bridge.llm_payload()

    @app.post("/character/respond")
    async def character_respond(request: SayRequest) -> dict[str, Any]:
        """
        Primary CERBERUS-facing endpoint.
        Returns a fully typed CharacterResponse (schema_version=1.0)
        ready for the integration/plan pipeline.
        """
        t0 = time.perf_counter()
        state = runtime.character_state()
        dialogue = runtime.generate_dialogue(request.text)
        emote_sel = runtime.emote_mapper.map_emote(
            current_mood=state.get("mood", "calm"),
            dialogue_intent=dialogue.get("intent"),
            suggested_emote_id=dialogue.get("emote_id"),
        )
        behavior = runtime.suggest_behavior(request.text)

        mood_str = state.get("mood", "calm")
        try:
            mood = MoodLabel(mood_str)
        except ValueError:
            mood = MoodLabel.CALM

        char_response = CharacterResponse(
            reply_text=dialogue.get("spoken_text"),
            emote_id=emote_sel.emote_id if hasattr(emote_sel, "emote_id") else emote_sel.get("emote_id"),
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

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        ledger.record("character.respond", {
            "response_id": char_response.response_id,
            "routine_id": char_response.routine_id,
            "emote_id": char_response.emote_id,
            "mood": char_response.mood.value,
            "intent": char_response.intent,
        }, elapsed_ms=elapsed_ms)

        _log.decision("character.respond", context={
            "response_id": char_response.response_id,
            "routine_id": char_response.routine_id,
            "emote_id": char_response.emote_id,
            "elapsed_ms": elapsed_ms,
        })

        # Publish typed WS event so the Web UI updates immediately
        ws_evt = WSEvent(
            event_type=WSEventType.DIALOGUE_GENERATED,
            payload={
                "response_id": char_response.response_id,
                "reply_text": char_response.reply_text,
                "emote_id": char_response.emote_id,
                "routine_id": char_response.routine_id,
                "mood": char_response.mood.value,
                "character": bridge.character_payload(),
            },
        )
        await events.publish(EventEnvelope(
            event_type=ws_evt.event_type.value,
            source="sweetiebot_api",
            payload=ws_evt.payload,
        ))

        return char_response.model_dump()

    @app.get("/events")
    def app_events() -> dict[str, Any]:
        return {"items": runtime.recent_trace_events(limit=20)}

    @app.websocket("/ws/events")
    async def websocket_events(ws: WebSocket) -> None:
        await ws.accept()
        queue = events.connect()
        try:
            # ── Snapshot (replay-safe, backward-compatible envelope) ───
            # Only ONE message is sent directly at connect time — the
            # snapshot.  All subsequent events (persona changes, dialogue
            # replies, integration events) arrive through the queue so
            # that tests and clients always know the message ordering.
            snap_payload = make_snapshot_payload(
                bridge=bridge,
                gate=gate,
                mapper=mapper,
                ledger=ledger,
            )

            await ws.send_json({
                "type": "events.snapshot",
                "source": "sweetiebot_api",
                "schema_version": "1.0",
                "replay_safe": True,
                "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "payload": {**snap_payload, "replay_safe": True},
            })

            # ── Live event stream ──────────────────────────────────────
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                except TimeoutError:
                    await ws.send_json(
                        EventEnvelope(
                            "events.keepalive",
                            "sweetiebot_api",
                            {
                                "character":   bridge.character_payload(),
                                "safety_mode": gate.safety_mode.value,
                                "event_type":  WSEventType.CHARACTER_STATE_UPDATED.value,
                            },
                        ).to_dict()
                    )
                    continue
                await ws.send_json(message)
        finally:
            events.disconnect(queue)

    # ── Nudge endpoints (Companion Web Interface) ──────────────────────
    # These replace the direct /character/routine and /character/emote calls
    # with a "gentle suggestion" layer.  Sweetie-Bot reacts first, then decides.

    @app.post("/character/nudge")
    async def nudge(request: NudgeRequest) -> dict[str, Any]:
        """
        Companion Web Interface nudge endpoint.

        Instead of directly commanding Sweetie-Bot, the web UI sends a nudge.
        Sweetie-Bot reacts with a micro-reaction (verbal + emote), then the
        decision matrix determines what she does next.

        The micro_reaction is what fires immediately.
        The suggested_action is a follow-on that passes through the safety gate.
        """
        if request.intent:
            normalized, payload = adapt_nudge_response(raw=request, bridge=bridge)
            await publish_canonical_nudge_event(events=events, payload=payload)
            await run_cerberus_stub(events=events, decision=payload["decision"])
            return {
                "reaction": payload["reaction"],
                "decision": payload["decision"],
                "nudge_type": normalized["intent"],
            }

        state = runtime.character_state()
        result = nudge_handler.handle(
            request.nudge_type,
            current_mood=state.get("mood", "calm"),
            active_routine=state.get("active_routine"),
            safe_mode=bool(state.get("safe_mode", False)),
            degraded_mode=bool(state.get("degraded_mode", False)),
        )

        normalized, payload = adapt_nudge_response(
            raw={"intent": result.nudge_type.value, "source": request.source, "note": request.note, "context": request.context},
            bridge=bridge,
        )

        payload["reaction"] = {
            "speech": result.micro_reaction.speech,
            "emote": result.micro_reaction.emote,
            "attention": payload.get("reaction", {}).get("attention", "forward"),
            "intensity": payload.get("reaction", {}).get("intensity", 0.5),
            "motion_hint": result.micro_reaction.motion_hint,
            "accessory": result.micro_reaction.accessory,
            "priority": result.micro_reaction.priority,
        }
        payload["decision"] = {
            **payload["decision"],
            "autonomy_decision": result.autonomy_decision.value,
            "suggested_action": result.suggested_action,
            "suppressed": result.suppressed,
            "state_category": result.state_category,
            "nudge_count_recent": result.nudge_count_recent,
            "notes": result.notes,
        }

        await publish_canonical_nudge_event(events=events, payload=payload)
        await run_cerberus_stub(events=events, decision=payload["decision"])

        ledger.record("nudge.received", {
            "nudge_type": result.nudge_type.value,
            "decision": result.autonomy_decision.value,
            "suggested_action": result.suggested_action,
            "suppressed": result.suppressed,
            "source": request.source,
        })
        runtime._emit_trace(
            "nudge_received",
            f"Nudge: {result.nudge_type.value} → {result.autonomy_decision.value}",
            payload=result.to_dict(),
        )

        response = result.to_dict()
        response["reaction"] = payload["reaction"]
        response["decision"] = payload["decision"]
        return response

    @app.get("/character/nudge/status")
    def nudge_status() -> dict[str, Any]:
        """Current nudge handler state and recent history."""
        return nudge_handler.snapshot()

    # ── Event ingestion endpoint ───────────────────────────────────────
    @app.post("/character/event")
    async def ingest_event(payload: dict[str, Any]) -> dict[str, Any]:
        """
        Ingest a raw event from any source into the event pipeline.

        Events are normalised, state is updated, and action_hints are returned.
        Safety-critical events (battery_critical, system_fault) automatically
        escalate the safety gate.

        Example events:
          {"kind": "person_detected", "person_id": "guest_1"}
          {"kind": "battery_low", "battery_pct": 18}
          {"kind": "proximity_alert", "distance_m": 0.3}
          {"kind": "system_fault", "fault_code": "motor_error", "severity": "critical"}
        """
        result = runtime.ingest_event(payload)
        if result.get("safety_escalation"):
            ws_mode_evt = EventEnvelope(
                "safety.mode.changed",
                "event_pipeline",
                {
                    "safety_mode": gate.safety_mode.value,
                    "escalation": result["safety_escalation"],
                    "event_kind": result["event"]["kind"],
                    "character": bridge.character_payload(),
                },
            )
            await events.publish(ws_mode_evt)
        return result

    @app.get("/character/events/recent")
    def recent_events(limit: int = 20) -> dict[str, Any]:
        """Recent events from the event pipeline."""
        return {"items": runtime.event_pipeline.recent_events(limit=limit)}

    # ── Expression endpoint ────────────────────────────────────────────
    @app.post("/character/express")
    async def express(payload: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a coordinated expression (speech + motion + emote + accessory)
        through the ExpressionCoordinator. Prevents channel overlap.

        Body: {speech?, motion?, emote?, accessory?, interrupt_motion?}
        motion must be a valid routine_id in the CERBERUS allowlist.
        """
        result = runtime.express(
            speech=payload.get("speech"),
            motion=payload.get("motion"),
            emote=payload.get("emote"),
            accessory=payload.get("accessory"),
            interrupt_motion=payload.get("interrupt_motion", False),
        )
        if result.get("ok"):
            await _publish_refresh(bridge, "persona.changed", "sweetiebot_expression",
                                   {"expression": result})
        return result

    @app.get("/character/expression/status")
    def expression_status() -> dict[str, Any]:
        """Current ExpressionCoordinator channel state."""
        return runtime.expression_coordinator.snapshot()

    return app


app = create_app()

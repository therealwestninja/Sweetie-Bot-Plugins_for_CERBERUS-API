from __future__ import annotations

from typing import Any, Callable

from sweetiebot.behavior.director import BehaviorDirector
from sweetiebot.dialogue.contracts import DialogueDirective, DialogueReply
from sweetiebot.mood.engine import MoodEngine
from sweetiebot.persona.loader import PERSONA_LIBRARY, load_persona, validate_persona
from sweetiebot.plugins import PluginRegistry
from sweetiebot.plugins.types import PluginType
from sweetiebot.plugins.builtins import RuleBasedDialogueProviderPlugin, RuleBasedEmoteMapperPlugin
from sweetiebot.routines.arbitrator import RoutineArbitrator
from sweetiebot.routines.registry import RoutineRegistry
from sweetiebot.state.manager import CharacterStateManager
from sweetiebot.telemetry.models import TraceEvent


class RuntimeState(dict):
    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in self.items():
            if hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result


class SweetieBotRuntime:
    def __init__(
        self,
        *,
        dialogue: RuleBasedDialogueProviderPlugin | None = None,
        routines: RoutineRegistry | None = None,
        plugins: PluginRegistry | None = None,
        plugin_registry: PluginRegistry | None = None,
    ) -> None:
        self.dialogue_provider = dialogue or RuleBasedDialogueProviderPlugin()
        self.emote_mapper = RuleBasedEmoteMapperPlugin()
        self.mood_engine = MoodEngine()
        self.behavior_director = BehaviorDirector()
        self.arbitrator = RoutineArbitrator()
        self.plugins = plugin_registry or plugins or PluginRegistry()
        if hasattr(self.plugins, "register_builtins"):
            self.plugins.register_builtins()
        self.routines = routines or RoutineRegistry()
        if hasattr(self.plugins, "iter_routine_payloads"):
            for routine_id, payload in self.plugins.iter_routine_payloads().items():
                self.routines.register(routine_id, payload)
        self.memory_store = None
        if hasattr(self.plugins, "get_memory_store"):
            try:
                self.memory_store = self.plugins.get_memory_store()
            except Exception:
                self.memory_store = None
        if self.memory_store is None:
            from sweetiebot.plugins.builtins.memory import InMemoryStorePlugin
            self.memory_store = InMemoryStorePlugin()
        self.state_manager = CharacterStateManager(memory_store=self.memory_store)
        self.persona_payload = validate_persona(PERSONA_LIBRARY["sweetiebot_default"])
        self.dialogue_rules = {
            "persona_id": self.persona_payload["id"],
            "dialogue_style": self.persona_payload["dialogue_style"],
            "default_emote": self.persona_payload["defaults"]["emote"],
            "default_accessory_scene": self.persona_payload["defaults"]["accessory_scene"],
        }
        self.state = RuntimeState(
            persona_id=self.persona_payload["id"],
            current_emote_id=self.persona_payload["defaults"]["emote"],
            current_routine_id=self.persona_payload["defaults"]["routine"],
            current_accessory_scene_id=self.persona_payload["defaults"]["accessory_scene"],
            safe_mode=False,
            degraded_mode=False,
            last_user_text=None,
            last_reply_text=None,
            last_intent=None,
            last_dialogue=None,
            last_emote=None,
            last_observations=[],
            last_speech=None,
            last_playback=None,
        )
        self._emit_trace("runtime_initialized", "Sweetie Bot runtime initialized")

    def _emit_trace(self, event_type: str, message: str, payload: dict[str, Any] | None = None) -> None:
        sink = self.plugins.get_telemetry_sink() if hasattr(self.plugins, "get_telemetry_sink") else None
        if sink is not None:
            sink.emit(TraceEvent(event_type=event_type, message=message, payload=payload or {}))

    def plugin_summary(self) -> list[dict[str, Any]]:
        return self.plugins.list_all() if hasattr(self.plugins, "list_all") else []

    def configure_plugins(self, payload: dict[str, Any]) -> list[str]:
        return self.plugins.configure_from_mapping(payload) if hasattr(self.plugins, "configure_from_mapping") else []

    def configure_plugins_from_file(self, path: str) -> list[str]:
        return self.plugins.configure_from_yaml(path) if hasattr(self.plugins, "configure_from_yaml") else []

    def configure_persona(self, payload: dict[str, Any]) -> RuntimeState:
        self.persona_payload = validate_persona(payload)
        self.state.persona_id = self.persona_payload["id"]
        self.state.current_emote_id = self.persona_payload["defaults"]["emote"]
        self.state.current_accessory_scene_id = self.persona_payload["defaults"]["accessory_scene"]
        self.state_manager.state.persona_id = self.persona_payload["id"]
        if self.persona_payload["id"] == "sweetiebot_convention":
            self.state_manager.set_mood("excited")
        self._emit_trace("persona_configured", "Persona configured", {"persona_id": self.state.persona_id})
        return self.state

    def load_persona_file(self, path: str) -> RuntimeState:
        payload = load_persona(path)
        return self.configure_persona(payload)

    def register_routine(self, routine_id: str, payload: dict[str, Any]) -> None:
        self.routines.register(routine_id, payload)

    def character_state(self) -> dict[str, Any]:
        snap = self.state_manager.snapshot()
        snap["persona_id"] = self.state.persona_id
        snap["active_emote"] = self.state.current_emote_id
        snap["active_routine"] = self.state.current_routine_id
        snap["accessory_scene"] = self.state.current_accessory_scene_id
        snap["safe_mode"] = self.state.safe_mode
        snap["degraded_mode"] = self.state.degraded_mode
        return snap

    def update_character_state(self, **kwargs: Any) -> dict[str, Any]:
        from sweetiebot.state.models import StateUpdate
        return self.state_manager.update(StateUpdate(**kwargs))

    def note_turn(self, user_text: str, reply_text: str, mood: str | None = None) -> dict[str, Any]:
        inferred = mood or self.mood_engine.infer_from_turn(user_text, reply_text, self.state_manager.state.mood)
        self.memory_store.put(__import__('sweetiebot.memory.models', fromlist=['MemoryRecord']).MemoryRecord(kind='user_input', content=user_text, source='runtime'))
        self.memory_store.put(__import__('sweetiebot.memory.models', fromlist=['MemoryRecord']).MemoryRecord(kind='assistant_reply', content=reply_text, source='runtime'))
        state = self.state_manager.note_turn(user_text, reply_text, mood=inferred)
        self._emit_trace("turn_noted", "Conversation turn recorded", {"mood": inferred})
        return state

    def recall(self, *, text: str | None = None, kind: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        query_cls = __import__('sweetiebot.memory.models', fromlist=['MemoryQuery']).MemoryQuery
        items = self.memory_store.query(query_cls(text=text, kind=kind, limit=limit))
        return [item.to_dict() for item in items]

    def apply_mood_event(self, event: str) -> dict[str, Any]:
        mood = self.mood_engine.apply_event(self.state_manager.state.mood, event)
        self.state_manager.set_mood(mood)
        self._emit_trace("mood_event_applied", "Mood event applied", {"event": event, "mood": mood})
        return {"mood": mood}

    def recent_trace_events(self, limit: int = 20) -> list[dict[str, Any]]:
        sink = self.plugins.get_telemetry_sink() if hasattr(self.plugins, "get_telemetry_sink") else None
        events = sink.recent_events(limit=limit) if sink else []
        return [event.to_dict() for event in events]

    def generate_dialogue(self, user_text: str) -> dict[str, Any]:
        result = self.dialogue_provider.generate_reply(
            user_text=user_text,
            current_mood=self.state_manager.state.mood,
            current_focus=self.state_manager.state.focus_target,
            active_routine=self.state.current_routine_id,
            safe_mode=self.state.safe_mode,
            degraded_mode=self.state.degraded_mode,
        )
        result_dict = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        emote = self.emote_mapper.map_emote(current_mood=self.state_manager.state.mood, dialogue_intent=result_dict["intent"], suggested_emote_id=result_dict.get("emote_id"))
        self.state.last_dialogue = result_dict
        self.state.last_reply_text = result_dict["spoken_text"]
        self.state["last_reply"] = result_dict["spoken_text"]
        self.state.last_intent = result_dict["intent"]
        self.state.last_user_text = user_text
        self.state.current_emote_id = emote.emote_id
        self.state.last_emote = emote.to_dict()
        self.state_manager.note_turn(user_text, result_dict["spoken_text"], mood=self.mood_engine.infer_from_turn(user_text, result_dict["spoken_text"], self.state_manager.state.mood))
        return result_dict

    def dialogue_status(self) -> dict[str, Any]:
        return {"last_dialogue": self.state.last_dialogue, "provider": "rule_based"}

    def emote_status(self) -> dict[str, Any]:
        return {"current_emote": self.state.current_emote_id, "last_emote": self.state.last_emote}

    def apply_attention(self, user_text: str) -> dict[str, Any]:
        plugin = self.plugins.get_attention_strategy() if hasattr(self.plugins, "get_attention_strategy") else None
        suggestion = plugin.suggest_attention(
            user_text=user_text,
            current_focus=self.state_manager.state.focus_target,
            current_mood=self.state_manager.state.mood,
            safe_mode=self.state.safe_mode,
            degraded_mode=self.state.degraded_mode,
        )
        self.state_manager.set_focus(suggestion.target)
        return {"suggestion": suggestion.to_dict(), "state": self.character_state()}

    def poll_perception(self) -> list[dict[str, Any]]:
        observations = []
        for plugin in (self.plugins.get_perception_sources() if hasattr(self.plugins, "get_perception_sources") else []):
            observations.extend(plugin.poll_observations())
        self.state["last_observations"] = [item.to_dict() for item in observations]
        for item in observations:
            self.memory_store.put(__import__('sweetiebot.memory.models', fromlist=['MemoryRecord']).MemoryRecord(kind='observation', content=item.value, source=item.source, metadata=item.to_dict()))
        return self.state["last_observations"]

    def apply_perception(self) -> dict[str, Any]:
        observations = self.poll_perception()
        if observations:
            self.state_manager.set_focus("guest")
        return {"observations": observations, "state": self.character_state()}

    def suggest_behavior(self, user_text: str) -> dict[str, Any]:
        return self.behavior_director.suggest(
            user_text=user_text,
            current_mood=self.state_manager.state.mood,
            focus_target=self.state_manager.state.focus_target,
            active_routine=self.state.current_routine_id,
            safe_mode=self.state.safe_mode,
            degraded_mode=self.state.degraded_mode,
        )

    def suggest_and_arbitrate_behavior(self, user_text: str) -> dict[str, Any]:
        behavior = self.suggest_behavior(user_text)
        arbitration = self.arbitrator.arbitrate(
            requested_routine=behavior.get("routine_id"),
            active_routine=self.state.current_routine_id,
            safe_mode=self.state.safe_mode,
            degraded_mode=self.state.degraded_mode,
        )
        return {"behavior": behavior, "routine_arbitration": arbitration}

    def apply_operator_stop(self) -> RuntimeState:
        self.state.current_routine_id = "return_to_neutral"
        self.state.current_emote_id = "calm_neutral"
        self.state.safe_mode = True
        return self.state

    def reset_neutral(self) -> RuntimeState:
        self.state.current_routine_id = "return_to_neutral"
        self.state.current_emote_id = self.persona_payload["defaults"]["emote"]
        self.state.current_accessory_scene_id = self.persona_payload["defaults"]["accessory_scene"]
        self.state.safe_mode = False
        return self.state

    def _reply_from_plugins(self, user_text: str) -> DialogueReply:
        runtime_context = {"persona_payload": self.persona_payload, "runtime_state": self.state.to_dict()}
        payload = self.plugins.run_dialogue(user_text=user_text, runtime_context=runtime_context)
        reply = DialogueReply.from_dict(payload).normalized()
        return self.plugins.apply_safety_policy(reply=reply, runtime_context=runtime_context)

    def handle_text(self, user_text: str) -> dict[str, Any]:
        reply = self._reply_from_plugins(user_text)
        directive = reply.directive
        routine_id = directive.routine_id
        if routine_id and routine_id not in self.routines.list_ids():
            directive.routine_id = None
            self.state.degraded_mode = True
        else:
            self.state.degraded_mode = False
        self.state.last_user_text = user_text
        self.state.last_reply_text = reply.text
        self.state.last_intent = reply.intent.value if hasattr(reply.intent, 'value') else str(reply.intent)
        self.state.current_emote_id = directive.emote_id or self.state.current_emote_id
        self.state.current_accessory_scene_id = directive.accessory_scene_id or self.state.current_accessory_scene_id
        self.state.current_routine_id = directive.routine_id or self.state.current_routine_id
        self.state.persona_id = self.persona_payload["id"]
        self.state.safe_mode = (reply.intent.value if hasattr(reply.intent, 'value') else str(reply.intent)) == "cancel"
        self.note_turn(user_text, reply.text)
        return {"reply": reply.to_dict(), "state": self.state.to_dict()}

    def say(self, text: str) -> dict[str, Any]:
        reply = self.generate_dialogue(text)
        spoken_text = reply["spoken_text"]
        tts = self.plugins.get_best_plugin("tts_provider") if hasattr(self.plugins, "get_best_plugin") else None
        audio = self.plugins.get_best_plugin("audio_output") if hasattr(self.plugins, "get_best_plugin") else None
        speech_payload = tts.synthesize(spoken_text) if tts else {"ok": False, "text": spoken_text}
        playback = audio.play(speech_payload) if audio else {"ok": False, "played_text": spoken_text}
        self.state.last_speech = {"text": spoken_text, **speech_payload}
        self.state.last_playback = playback
        return RuntimeState(intent=reply["intent"], spoken_text=spoken_text, reply=spoken_text, provider="local", speech=speech_payload, playback=playback, audio={"sink": "disabled" if not playback.get("ok") else playback.get("output", playback.get("sink", "disabled"))}, emote_id=self.state.current_emote_id)

    def speak(self, text: str) -> RuntimeState:
        return self.say(text)

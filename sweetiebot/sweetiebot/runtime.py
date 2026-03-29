from __future__ import annotations

from typing import Dict, Any, List, Optional

from sweetiebot.attention.models import AttentionSuggestion
from sweetiebot.behavior.director import BehaviorDirector
from sweetiebot.dialogue.models import DialogueResponse
from sweetiebot.emotes.models import EmoteSelection
from sweetiebot.memory.models import MemoryQuery, MemoryRecord
from sweetiebot.mood.engine import MoodEngine
from sweetiebot.plugins.builtins.attention import RuleBasedAttentionStrategyPlugin
from sweetiebot.plugins.builtins.dialogue import RuleBasedDialogueProviderPlugin
from sweetiebot.plugins.builtins.emotes import RuleBasedEmoteMapperPlugin
from sweetiebot.plugins.builtins.memory import InMemoryStorePlugin
from sweetiebot.plugins.builtins.perception import MockPerceptionSourcePlugin
from sweetiebot.plugins.builtins.telemetry import InMemoryTelemetrySinkPlugin
from sweetiebot.plugins.registry import PluginRegistry
from sweetiebot.routines.arbitrator import RoutineArbitrator
from sweetiebot.state.manager import CharacterStateManager
from sweetiebot.state.models import StateUpdate
from sweetiebot.telemetry.models import TraceEvent


class SweetieBotRuntime:
    def __init__(self) -> None:
        self.registry = PluginRegistry()
        self.registry.register(InMemoryStorePlugin())
        self.registry.register(InMemoryTelemetrySinkPlugin())
        self.registry.register(RuleBasedAttentionStrategyPlugin())
        self.registry.register(MockPerceptionSourcePlugin())
        self.registry.register(RuleBasedDialogueProviderPlugin())
        self.registry.register(RuleBasedEmoteMapperPlugin())
        self.state: Dict[str, Any] = {
            "safe_mode": False,
            "degraded_mode": False,
            "last_input": None,
            "last_reply": None,
            "last_observations": [],
            "last_dialogue": None,
            "last_emote": None,
        }
        self.state_manager = CharacterStateManager(memory_store=self.registry.get_memory_store())
        self.mood_engine = MoodEngine(default_mood=self.state_manager.state.mood)
        self.behavior_director = BehaviorDirector()
        self.routine_arbitrator = RoutineArbitrator()
        self.emit_trace("runtime_initialized", "Sweetie Bot runtime initialized", source="runtime")

    def emit_trace(
        self,
        event_type: str,
        message: str,
        *,
        source: str = "runtime",
        level: str = "info",
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        sink = self.registry.get_telemetry_sink()
        event = TraceEvent(
            event_type=event_type,
            message=message,
            source=source,
            level=level,
            payload=payload or {},
        )
        if sink is None:
            return event.to_dict()
        return sink.emit(event).to_dict()

    def recent_trace_events(self, limit: int = 25) -> List[Dict[str, Any]]:
        sink = self.registry.get_telemetry_sink()
        if sink is None:
            return []
        return [event.to_dict() for event in sink.recent_events(limit=limit)]

    def remember(self, kind: str, content: str, source: str = "runtime", **kwargs) -> Dict[str, Any]:
        store = self.registry.get_memory_store()
        if store is None:
            self.state["degraded_mode"] = True
            raise RuntimeError("No memory store plugin registered")
        record = MemoryRecord(kind=kind, content=content, source=source, **kwargs)
        stored = store.put(record)
        self.emit_trace(
            "memory_written",
            f"Memory record stored: {kind}",
            source="memory",
            payload={"kind": kind, "source": source, "record_id": stored.record_id},
        )
        return stored.to_dict()

    def recall(
        self,
        text: Optional[str] = None,
        kind: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        store = self.registry.get_memory_store()
        if store is None:
            self.state["degraded_mode"] = True
            return []
        records = store.query(MemoryQuery(text=text, kind=kind, scope=scope, limit=limit))
        self.emit_trace(
            "memory_recalled",
            "Memory query executed",
            source="memory",
            payload={"text": text, "kind": kind, "scope": scope, "limit": limit, "results": len(records)},
        )
        return [r.to_dict() for r in records]

    def map_emote(
        self,
        *,
        dialogue_intent: Optional[str] = None,
        suggested_emote_id: Optional[str] = None,
        behavior_action: Optional[str] = None,
    ) -> Dict[str, Any]:
        mapper = self.registry.get_emote_mapper()
        state = self.state_manager.state

        if mapper is None:
            selection = EmoteSelection(
                emote_id="calm_neutral",
                reason="no_emote_mapper_available",
                intensity=0.3,
                source="runtime",
                confidence=0.2,
            )
        else:
            selection = mapper.map_emote(
                current_mood=state.mood,
                dialogue_intent=dialogue_intent,
                suggested_emote_id=suggested_emote_id,
                behavior_action=behavior_action,
                safe_mode=state.safe_mode,
                degraded_mode=state.degraded_mode,
            )

        result = selection.to_dict()
        self.state["last_emote"] = result
        self.state_manager.set_emote(result["emote_id"])
        self.remember(
            kind="emote_selection",
            content=result["emote_id"],
            source=result["source"],
            tags=["emote"],
            metadata=result,
        )
        self.emit_trace(
            "emote_mapped",
            f"Emote mapped: {result['emote_id']}",
            source="emote_mapper",
            payload={"selection": result},
        )
        return result

    def emote_status(self) -> Dict[str, Any]:
        mapper = self.registry.get_emote_mapper()
        return {
            "mapper": mapper.healthcheck() if mapper else {"healthy": False, "reason": "missing"},
            "last_emote": self.state.get("last_emote"),
            "current_emote": self.state_manager.state.active_emote,
        }

    def generate_dialogue(self, user_text: Optional[str]) -> Dict[str, Any]:
        provider = self.registry.get_dialogue_provider()
        state = self.state_manager.state
        if provider is None:
            response = DialogueResponse(
                spoken_text="I'm not ready to answer right now.",
                intent="reply",
                emote_id="calm_neutral",
                confidence=0.2,
                source="runtime",
                metadata={"reason": "no_dialogue_provider"},
            )
        else:
            response = provider.generate_reply(
                user_text=user_text,
                current_mood=state.mood,
                current_focus=state.focus_target,
                active_routine=state.active_routine,
                safe_mode=state.safe_mode,
                degraded_mode=state.degraded_mode,
            )

        result = response.to_dict()
        self.state["last_dialogue"] = result
        self.state["last_input"] = user_text
        self.state["last_reply"] = result["spoken_text"]
        self.state_manager.note_turn(user_text or "", result["spoken_text"], mood=state.mood)
        self.remember(
            kind="dialogue_response",
            content=result["spoken_text"],
            source=result["source"],
            tags=["dialogue"],
            metadata=result,
        )
        self.emit_trace(
            "dialogue_generated",
            f"Dialogue generated: {result['intent']}",
            source="dialogue_provider",
            payload={"input": user_text, "response": result},
        )
        self.map_emote(
            dialogue_intent=result.get("intent"),
            suggested_emote_id=result.get("emote_id"),
        )
        return result

    def dialogue_status(self) -> Dict[str, Any]:
        provider = self.registry.get_dialogue_provider()
        return {
            "provider": provider.healthcheck() if provider else {"healthy": False, "reason": "missing"},
            "last_dialogue": self.state.get("last_dialogue"),
        }

    def poll_perception(self) -> List[Dict[str, Any]]:
        observations: List[Dict[str, Any]] = []
        for source in self.registry.get_perception_sources():
            polled = source.poll_observations()
            observations.extend([obs.to_dict() for obs in polled])
        self.state["last_observations"] = observations
        self.emit_trace(
            "perception_polled",
            "Perception sources polled",
            source="perception",
            payload={"count": len(observations), "observations": observations},
        )
        for obs in observations:
            self.remember(
                kind="observation",
                content=f"{obs['observation_type']}={obs['value']}",
                source=obs["source"],
                tags=["perception"],
                metadata=obs,
            )
        return observations

    def apply_perception(self) -> Dict[str, Any]:
        observations = self.poll_perception()
        applied_focus = None
        for obs in observations:
            if obs["observation_type"] == "presence" and obs["value"] == "guest_present":
                applied_focus = "guest"
                break
            if obs["observation_type"] == "attention_hint":
                applied_focus = obs["value"]
                break
        if applied_focus:
            self.state_manager.set_focus(applied_focus)
            self.emit_trace(
                "perception_applied",
                f"Perception updated focus to {applied_focus}",
                source="perception",
                payload={"focus_target": applied_focus, "observations": observations},
            )
        return {
            "observations": observations,
            "state": self.character_state(),
        }

    def perception_status(self) -> Dict[str, Any]:
        sources = self.registry.get_perception_sources()
        return {
            "sources": [source.healthcheck() for source in sources],
            "last_observations": self.state.get("last_observations", []),
        }

    def note_turn(self, user_text: str, reply_text: str, mood: Optional[str] = None) -> None:
        inferred_mood = mood or self.mood_engine.infer_from_turn(
            user_text=user_text,
            reply_text=reply_text,
            current_mood=self.state_manager.state.mood,
        )
        self.state["last_input"] = user_text
        self.state["last_reply"] = reply_text
        self.remember(kind="user_input", content=user_text, source="dialogue", tags=["turn"])
        self.remember(kind="assistant_reply", content=reply_text, source="dialogue", tags=["turn"])
        self.state_manager.note_turn(user_text, reply_text, mood=inferred_mood)
        self.remember(
            kind="mood_inference",
            content=f"Mood inferred as {inferred_mood}",
            source="mood_engine",
            tags=["mood"],
            metadata={"user_text": user_text, "reply_text": reply_text, "mood": inferred_mood},
        )
        self.emit_trace(
            "turn_noted",
            "Dialogue turn recorded",
            source="dialogue",
            payload={"user_text": user_text, "reply_text": reply_text, "mood": inferred_mood},
        )

    def apply_mood_event(self, event: str) -> Dict[str, Any]:
        new_mood = self.mood_engine.apply_event(self.state_manager.state.mood, event)
        state = self.state_manager.set_mood(new_mood)
        self.remember(
            kind="mood_event",
            content=f"Mood event {event} -> {new_mood}",
            source="mood_engine",
            tags=["mood"],
            metadata={"event": event, "mood": new_mood},
        )
        self.emit_trace(
            "mood_event_applied",
            f"Mood event applied: {event}",
            source="mood_engine",
            payload={"event": event, "new_mood": new_mood},
        )
        return state

    def decay_mood(self) -> Dict[str, Any]:
        new_mood = self.mood_engine.decay(self.state_manager.state.mood)
        state = self.state_manager.set_mood(new_mood)
        self.remember(
            kind="mood_decay",
            content=f"Mood decayed to {new_mood}",
            source="mood_engine",
            tags=["mood"],
            metadata={"mood": new_mood},
        )
        self.emit_trace(
            "mood_decayed",
            "Mood decay applied",
            source="mood_engine",
            payload={"new_mood": new_mood},
        )
        return state

    def mood_status(self) -> Dict[str, Any]:
        return {
            "current_mood": self.state_manager.state.mood,
            "engine": self.mood_engine.snapshot(),
        }

    def suggest_attention(self, user_text: Optional[str] = None) -> Dict[str, Any]:
        state = self.state_manager.state
        strategy = self.registry.get_attention_strategy()
        if strategy is None:
            suggestion = AttentionSuggestion(
                target=state.focus_target,
                reason="no_attention_strategy_available",
                priority="low",
                confidence=0.2,
                source="runtime",
            )
            result = suggestion.to_dict()
        else:
            result = strategy.suggest_attention(
                user_text=user_text or state.last_input,
                current_focus=state.focus_target,
                current_mood=state.mood,
                safe_mode=state.safe_mode,
                degraded_mode=state.degraded_mode,
            ).to_dict()
        self.emit_trace(
            "attention_suggested",
            f"Attention suggested: {result.get('target')}",
            source="attention_strategy",
            payload={"input": user_text, "suggestion": result},
        )
        return result

    def apply_attention(self, user_text: Optional[str] = None) -> Dict[str, Any]:
        suggestion = self.suggest_attention(user_text=user_text)
        self.state_manager.set_focus(suggestion.get("target"))
        self.emit_trace(
            "attention_applied",
            f"Attention applied: {suggestion.get('target')}",
            source="attention_strategy",
            payload={"suggestion": suggestion, "state": self.character_state()},
        )
        return {
            "suggestion": suggestion,
            "state": self.character_state(),
        }

    def attention_status(self) -> Dict[str, Any]:
        strategy = self.registry.get_attention_strategy()
        return {
            "strategy": strategy.healthcheck() if strategy else {"healthy": False, "reason": "missing"},
            "current_focus": self.state_manager.state.focus_target,
            "suggested_from_state": self.suggest_attention(),
        }

    def suggest_behavior(self, user_text: Optional[str] = None) -> Dict[str, Any]:
        state = self.state_manager.state
        behavior = self.behavior_director.suggest(
            user_text=user_text or state.last_input,
            current_mood=state.mood,
            focus_target=state.focus_target,
            active_routine=state.active_routine,
            safe_mode=state.safe_mode,
            degraded_mode=state.degraded_mode,
        )
        self.remember(
            kind="behavior_suggestion",
            content=f"Behavior suggested: {behavior['action']}",
            source="behavior_director",
            tags=["behavior"],
            metadata={"input": user_text, "behavior": behavior},
        )
        self.emit_trace(
            "behavior_suggested",
            f"Behavior suggested: {behavior['action']}",
            source="behavior_director",
            payload={"input": user_text, "behavior": behavior},
        )
        self.map_emote(
            behavior_action=behavior.get("action"),
            suggested_emote_id=behavior.get("emote_id"),
        )
        return behavior

    def arbitrate_routine(self, requested_routine: Optional[str]) -> Dict[str, Any]:
        state = self.state_manager.state
        decision = self.routine_arbitrator.arbitrate(
            requested_routine=requested_routine,
            active_routine=state.active_routine,
            safe_mode=state.safe_mode,
            degraded_mode=state.degraded_mode,
        )
        if decision["allowed"]:
            self.state_manager.set_routine(decision["routine_id"])
        self.remember(
            kind="routine_arbitration",
            content=f"Routine arbitration: {decision['reason']}",
            source="routine_arbitrator",
            tags=["routine"],
            metadata={"requested_routine": requested_routine, "decision": decision},
        )
        self.emit_trace(
            "routine_arbitrated",
            f"Routine arbitration result: {decision['reason']}",
            source="routine_arbitrator",
            payload={"requested_routine": requested_routine, "decision": decision},
        )
        return decision

    def suggest_and_arbitrate_behavior(self, user_text: Optional[str] = None) -> Dict[str, Any]:
        behavior = self.suggest_behavior(user_text=user_text)
        arbitration = self.arbitrate_routine(behavior.get("routine_id"))
        self.emit_trace(
            "behavior_arbitrated",
            "Behavior suggestion passed through routine arbitration",
            source="behavior_director",
            payload={"behavior": behavior, "arbitration": arbitration},
        )
        return {
            "behavior": behavior,
            "routine_arbitration": arbitration,
        }

    def behavior_status(self) -> Dict[str, Any]:
        return {
            "director": self.behavior_director.snapshot(),
            "suggested_from_state": self.suggest_behavior(),
            "routine_arbitration": self.routine_arbitrator.snapshot(),
        }

    def telemetry_status(self) -> Dict[str, Any]:
        sink = self.registry.get_telemetry_sink()
        return {
            "sink": sink.healthcheck() if sink else {"healthy": False, "reason": "missing"},
            "recent_events": self.recent_trace_events(limit=10),
        }

    def update_character_state(self, **kwargs) -> Dict[str, Any]:
        state = self.state_manager.update(StateUpdate(**kwargs))
        self.emit_trace(
            "state_updated",
            "Character state updated",
            source="state_manager",
            payload={"updates": kwargs, "state": state},
        )
        return state

    def character_state(self) -> Dict[str, Any]:
        return self.state_manager.snapshot()

    def runtime_health(self) -> Dict[str, Any]:
        store = self.registry.get_memory_store()
        return {
            "state": self.state,
            "character_state": self.character_state(),
            "dialogue": self.dialogue_status(),
            "emotes": self.emote_status(),
            "mood": self.mood_status(),
            "perception": self.perception_status(),
            "attention": self.attention_status(),
            "behavior": self.behavior_status(),
            "telemetry": self.telemetry_status(),
            "plugins": self.registry.plugin_summary(),
            "memory": store.healthcheck() if store else {"healthy": False, "reason": "missing"},
        }

from __future__ import annotations

from typing import Dict, Any, List, Optional

from sweetiebot.behavior.director import BehaviorDirector
from sweetiebot.memory.models import MemoryQuery, MemoryRecord
from sweetiebot.mood.engine import MoodEngine
from sweetiebot.plugins.builtins.memory import InMemoryStorePlugin
from sweetiebot.plugins.registry import PluginRegistry
from sweetiebot.state.manager import CharacterStateManager
from sweetiebot.state.models import StateUpdate


class SweetieBotRuntime:
    def __init__(self) -> None:
        self.registry = PluginRegistry()
        self.registry.register(InMemoryStorePlugin())
        self.state: Dict[str, Any] = {
            "safe_mode": False,
            "degraded_mode": False,
            "last_input": None,
            "last_reply": None,
        }
        self.state_manager = CharacterStateManager(memory_store=self.registry.get_memory_store())
        self.mood_engine = MoodEngine(default_mood=self.state_manager.state.mood)
        self.behavior_director = BehaviorDirector()

    def remember(self, kind: str, content: str, source: str = "runtime", **kwargs) -> Dict[str, Any]:
        store = self.registry.get_memory_store()
        if store is None:
            self.state["degraded_mode"] = True
            raise RuntimeError("No memory store plugin registered")
        record = MemoryRecord(kind=kind, content=content, source=source, **kwargs)
        stored = store.put(record)
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
        return [r.to_dict() for r in records]

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
        return state

    def mood_status(self) -> Dict[str, Any]:
        return {
            "current_mood": self.state_manager.state.mood,
            "engine": self.mood_engine.snapshot(),
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
        return behavior

    def behavior_status(self) -> Dict[str, Any]:
        return {
            "director": self.behavior_director.snapshot(),
            "suggested_from_state": self.suggest_behavior(),
        }

    def update_character_state(self, **kwargs) -> Dict[str, Any]:
        return self.state_manager.update(StateUpdate(**kwargs))

    def character_state(self) -> Dict[str, Any]:
        return self.state_manager.snapshot()

    def runtime_health(self) -> Dict[str, Any]:
        store = self.registry.get_memory_store()
        return {
            "state": self.state,
            "character_state": self.character_state(),
            "mood": self.mood_status(),
            "behavior": self.behavior_status(),
            "plugins": self.registry.plugin_summary(),
            "memory": store.healthcheck() if store else {"healthy": False, "reason": "missing"},
        }

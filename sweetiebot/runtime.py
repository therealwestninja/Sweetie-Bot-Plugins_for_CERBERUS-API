from __future__ import annotations

from typing import Dict, Any, List, Optional

from sweetiebot.memory.models import MemoryQuery, MemoryRecord
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
        self.state["last_input"] = user_text
        self.state["last_reply"] = reply_text
        self.remember(kind="user_input", content=user_text, source="dialogue", tags=["turn"])
        self.remember(kind="assistant_reply", content=reply_text, source="dialogue", tags=["turn"])
        self.state_manager.note_turn(user_text, reply_text, mood=mood)

    def update_character_state(self, **kwargs) -> Dict[str, Any]:
        return self.state_manager.update(StateUpdate(**kwargs))

    def character_state(self) -> Dict[str, Any]:
        return self.state_manager.snapshot()

    def runtime_health(self) -> Dict[str, Any]:
        store = self.registry.get_memory_store()
        return {
            "state": self.state,
            "character_state": self.character_state(),
            "plugins": self.registry.plugin_summary(),
            "memory": store.healthcheck() if store else {"healthy": False, "reason": "missing"},
        }

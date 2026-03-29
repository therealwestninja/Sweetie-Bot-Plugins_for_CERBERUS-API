from __future__ import annotations

from typing import Any, Dict, List, Optional

from sweetiebot.attention.models import AttentionSuggestion
from sweetiebot.dialogue.models import DialogueResponse
from sweetiebot.emotes.models import EmoteSelection
from sweetiebot.memory.models import MemoryQuery, MemoryRecord
from sweetiebot.perception.models import Observation
from sweetiebot.telemetry.models import TraceEvent


class BasePlugin:
    plugin_id: str = "base.plugin"
    plugin_type: str = "base"

    def manifest(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_type": self.plugin_type,
            "version": "0.1.0",
            "healthy": True,
            "capabilities": [],
        }

    def configure(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def healthcheck(self) -> Dict[str, Any]:
        return {"healthy": True, "plugin_id": self.plugin_id}

    def shutdown(self) -> None:
        return None


class MemoryStorePlugin(BasePlugin):
    plugin_type = "memory_store"

    def put(self, record: MemoryRecord) -> MemoryRecord:
        raise NotImplementedError

    def query(self, query: MemoryQuery) -> List[MemoryRecord]:
        raise NotImplementedError

    def recent(self, limit: int = 10) -> List[MemoryRecord]:
        return self.query(MemoryQuery(limit=limit))


class TelemetrySinkPlugin(BasePlugin):
    plugin_type = "telemetry_sink"

    def emit(self, event: TraceEvent) -> TraceEvent:
        raise NotImplementedError

    def recent_events(self, limit: int = 25) -> List[TraceEvent]:
        raise NotImplementedError


class AttentionStrategyPlugin(BasePlugin):
    plugin_type = "attention_strategy"

    def suggest_attention(
        self,
        *,
        user_text: Optional[str],
        current_focus: Optional[str],
        current_mood: str,
        safe_mode: bool = False,
        degraded_mode: bool = False,
    ) -> AttentionSuggestion:
        raise NotImplementedError


class PerceptionSourcePlugin(BasePlugin):
    plugin_type = "perception_source"

    def poll_observations(self) -> List[Observation]:
        raise NotImplementedError


class DialogueProviderPlugin(BasePlugin):
    plugin_type = "dialogue_provider"

    def generate_reply(
        self,
        *,
        user_text: Optional[str],
        current_mood: str,
        current_focus: Optional[str],
        active_routine: Optional[str],
        safe_mode: bool = False,
        degraded_mode: bool = False,
    ) -> DialogueResponse:
        raise NotImplementedError


class EmoteMapperPlugin(BasePlugin):
    plugin_type = "emote_mapper"

    def map_emote(
        self,
        *,
        current_mood: str,
        dialogue_intent: Optional[str] = None,
        suggested_emote_id: Optional[str] = None,
        behavior_action: Optional[str] = None,
        safe_mode: bool = False,
        degraded_mode: bool = False,
    ) -> EmoteSelection:
        raise NotImplementedError

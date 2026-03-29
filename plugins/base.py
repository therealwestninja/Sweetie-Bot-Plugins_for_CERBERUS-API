from __future__ import annotations

from typing import Any, Dict, List, Optional

from sweetiebot.attention.models import AttentionSuggestion
from sweetiebot.dialogue.contracts import DialogueReply
from sweetiebot.dialogue.models import DialogueResponse
from sweetiebot.memory.models import MemoryQuery, MemoryRecord
from sweetiebot.perception.models import Observation
from sweetiebot.plugins.health import PluginHealthCheck, PluginHealthStatus
from sweetiebot.plugins.manifest import PluginManifest
from sweetiebot.plugins.types import PluginType
from sweetiebot.telemetry.models import TraceEvent


class PluginError(RuntimeError):
    pass


class BasePlugin:
    plugin_id: str = "base.plugin"
    plugin_type: str | PluginType = PluginType.ASSET_PACK
    priority: int = 100

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def manifest(self) -> PluginManifest:
        plugin_type = self.plugin_type if isinstance(self.plugin_type, PluginType) else PluginType(str(self.plugin_type))
        return PluginManifest(
            plugin_id=self.plugin_id,
            plugin_type=plugin_type,
            priority=self.priority,
            display_name=self.plugin_id,
        )

    def configure(self, config: Dict[str, Any] | None = None) -> None:
        if config:
            self.config.update(config)

    def healthcheck(self) -> Dict[str, Any] | PluginHealthCheck:
        return PluginHealthCheck(plugin_id=self.manifest().plugin_id, status=PluginHealthStatus.HEALTHY)

    def shutdown(self) -> None:
        return None


class MemoryStorePlugin(BasePlugin):
    plugin_type = PluginType.MEMORY_STORE

    def put(self, record: MemoryRecord) -> MemoryRecord:
        raise NotImplementedError

    def query(self, query: MemoryQuery) -> List[MemoryRecord]:
        raise NotImplementedError

    def recent(self, limit: int = 10) -> List[MemoryRecord]:
        return self.query(MemoryQuery(limit=limit))


class TelemetrySinkPlugin(BasePlugin):
    plugin_type = PluginType.TELEMETRY_SINK

    def emit(self, event: TraceEvent) -> TraceEvent:
        raise NotImplementedError

    def recent_events(self, limit: int = 25) -> List[TraceEvent]:
        raise NotImplementedError


class AttentionStrategyPlugin(BasePlugin):
    plugin_type = PluginType.ATTENTION_STRATEGY

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
    plugin_type = PluginType.PERCEPTION_SOURCE

    def poll_observations(self) -> List[Observation]:
        raise NotImplementedError


class DialogueProviderPlugin(BasePlugin):
    plugin_type = PluginType.DIALOGUE_PROVIDER

    def generate_reply(self, *args: Any, **kwargs: Any) -> DialogueResponse:
        raise NotImplementedError


class EmoteMapperPlugin(BasePlugin):
    plugin_type = PluginType.EMOTE_MAPPER

    def map_emote(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class RoutinePackPlugin(BasePlugin):
    plugin_type = PluginType.ROUTINE_PACK

    def list_routines(self) -> List[str]:
        return [item.get("routine_id", "") for item in self.get_routines()]

    def get_routines(self) -> List[Dict[str, Any]]:
        raise NotImplementedError


class SafetyPolicyPlugin(BasePlugin):
    plugin_type = PluginType.SAFETY_POLICY

    def apply(self, reply: DialogueReply, context: Dict[str, Any] | None = None) -> DialogueReply:
        raise NotImplementedError


class TTSProviderPlugin(BasePlugin):
    plugin_type = PluginType.TTS_PROVIDER

    def synthesize(self, text: str, voice_profile: Optional[str] = None, voice: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError


class AudioOutputPlugin(BasePlugin):
    plugin_type = PluginType.AUDIO_OUTPUT

    def play(self, audio_payload: Dict[str, Any] | str) -> Dict[str, Any]:
        raise NotImplementedError

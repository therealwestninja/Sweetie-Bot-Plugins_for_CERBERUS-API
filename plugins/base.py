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


# ---------------------------------------------------------------------------
# Integration layer plugin base classes
# These define the extension points for the Sweetie-Bot ↔ CERBERUS pipeline.
# Third-party developers can subclass these to provide custom mapping logic,
# safety policies, or memory context strategies.
# ---------------------------------------------------------------------------

class CerberusMapperPlugin(BasePlugin):
    """
    Translates a CharacterResponse into an ordered list of CERBERUS commands.

    Implementations must be fail-closed: unknown IDs must be rejected, never
    passed through. The ``plan()`` method must never raise; it returns a
    rejected plan instead.

    Capabilities to advertise in manifest:
        "allowlist_routines", "allowlist_emotes", "allowlist_accessories",
        "dry_run"
    """
    plugin_type = PluginType.CERBERUS_MAPPER

    def plan(
        self,
        response: Any,
        *,
        safety_mode: Any = None,
        dry_run: Optional[bool] = None,
    ) -> Any:
        """Return an IntegrationPlan for the given CharacterResponse."""
        raise NotImplementedError

    def validate(self, response: Any) -> Dict[str, Any]:
        """Validate without mutating state. Returns ValidationResult-compatible dict."""
        raise NotImplementedError

    def capabilities(self, safety_mode: Any = None) -> Any:
        """Return a CapabilityManifest describing what this mapper supports."""
        raise NotImplementedError

    def snapshot(self) -> Dict[str, Any]:
        """Return a serialisable snapshot of current mapper state."""
        raise NotImplementedError


class SafetyGatePlugin(BasePlugin):
    """
    Guards a CharacterResponse before it reaches the CERBERUS mapper.

    Implementations must be fail-closed: when in doubt, block.
    The gate must never raise on ``check()``; it returns a GateResult instead.

    Capabilities to advertise in manifest:
        "rate_limiting", "mode_aware", "operator_override", "audit_log"
    """
    plugin_type = PluginType.SAFETY_GATE

    def check(self, response: Any, *, operator_override: bool = False) -> Any:
        """Evaluate the response and return a GateResult."""
        raise NotImplementedError

    def validate_only(self, response: Any) -> Any:
        """Read-only check — no state is mutated. Returns ValidationResult-compat dict."""
        raise NotImplementedError

    def set_safety_mode(self, mode: Any) -> None:
        """Change the gate's operating mode (NORMAL/SAFE/DEGRADED/EMERGENCY)."""
        raise NotImplementedError

    def set_operator_override(self, active: bool) -> None:
        """Enable or disable the blanket operator override flag."""
        raise NotImplementedError

    @property
    def safety_mode(self) -> Any:
        """Current safety mode."""
        raise NotImplementedError

    def snapshot(self) -> Dict[str, Any]:
        """Return a serialisable snapshot of current gate state."""
        raise NotImplementedError

    def recent_audit(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent gate audit log entries."""
        raise NotImplementedError


class MemoryContextPlugin(BasePlugin):
    """
    Builds a concise natural-language context string from recent memory records
    so the dialogue / behavior layers can avoid repeating themselves and
    reference earlier exchanges naturally.

    Capabilities to advertise in manifest:
        "context_summary", "recent_commands"
    """
    plugin_type = PluginType.MEMORY_CONTEXT

    def build_context_summary(
        self,
        records: List[Dict[str, Any]],
        *,
        current_mood: str = "calm",
        current_routine: Optional[str] = None,
        max_chars: int = 400,
    ) -> str:
        """Return a natural-language summary of recent memory records."""
        raise NotImplementedError

    def extract_recent_commands(
        self,
        records: List[Dict[str, Any]],
        *,
        limit: int = 5,
    ) -> Dict[str, List[str]]:
        """Return recently used routine/emote IDs from memory."""
        raise NotImplementedError


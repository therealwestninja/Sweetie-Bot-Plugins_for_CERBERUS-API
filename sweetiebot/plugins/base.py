from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .health import PluginHealthCheck, PluginHealthStatus
from .manifest import PluginManifest
from .types import PluginFamily


class PluginError(RuntimeError):
    """Base exception for plugin failures."""


class BasePlugin:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config: Dict[str, Any] = config or {}

    @classmethod
    def manifest(cls) -> PluginManifest:
        raise NotImplementedError

    def configure(self, config: Dict[str, Any]) -> None:
        self.config.update(config)

    def validate(self) -> None:
        return None

    def healthcheck(self) -> PluginHealthCheck:
        manifest = self.manifest()
        return PluginHealthCheck(
            plugin_id=manifest.plugin_id,
            status=PluginHealthStatus.HEALTHY,
            summary="Plugin is healthy.",
        )

    def shutdown(self) -> None:
        return None


class DialogueProviderPlugin(BasePlugin):
    @classmethod
    def family(cls) -> PluginFamily:
        return PluginFamily.DIALOGUE_PROVIDER

    def generate_reply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class RoutinePackPlugin(BasePlugin):
    @classmethod
    def family(cls) -> PluginFamily:
        return PluginFamily.ROUTINE_PACK

    def get_routines(self) -> Dict[str, Any]:
        raise NotImplementedError


class SafetyPolicyPlugin(BasePlugin):
    @classmethod
    def family(cls) -> PluginFamily:
        return PluginFamily.SAFETY_POLICY

    def apply(self, reply: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return reply


class TTSProviderPlugin(BasePlugin):
    @classmethod
    def family(cls) -> PluginFamily:
        return PluginFamily.TTS_PROVIDER

    def synthesize(self, text: str, voice_profile: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError


class AudioOutputPlugin(BasePlugin):
    @classmethod
    def family(cls) -> PluginFamily:
        return PluginFamily.AUDIO_OUTPUT

    def play(self, audio_payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

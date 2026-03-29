from __future__ import annotations

from typing import Any, Dict, Optional

from sweetiebot.plugins.base import AudioOutputPlugin, TTSProviderPlugin
from sweetiebot.plugins.health import PluginHealthCheck, PluginHealthStatus
from sweetiebot.plugins.manifest import PluginManifest
from sweetiebot.plugins.types import PluginFamily


class MockTTSProviderPlugin(TTSProviderPlugin):
    @classmethod
    def manifest(cls) -> PluginManifest:
        return PluginManifest(
            plugin_id="sweetiebot.mock_tts",
            family=PluginFamily.TTS_PROVIDER,
            display_name="Mock TTS Provider",
            description="Returns structured mock speech payloads for safe local testing.",
            capabilities=["synthesize_text", "mock_audio_payload"],
            priority=100,
        )

    def synthesize(self, text: str, voice_profile: Optional[str] = None) -> Dict[str, Any]:
        cleaned = (text or "").strip()
        voice = voice_profile or self.config.get("default_voice", "sweetie_mock_voice")
        return {
            "ok": True,
            "provider": self.manifest().plugin_id,
            "voice_profile": voice,
            "text": cleaned,
            "audio_format": "text/mock-audio",
            "audio_bytes": cleaned.encode("utf-8"),
            "duration_ms": max(250, min(len(cleaned) * 45, 8000)),
            "cached": False,
        }

    def healthcheck(self) -> PluginHealthCheck:
        return PluginHealthCheck(
            plugin_id=self.manifest().plugin_id,
            status=PluginHealthStatus.HEALTHY,
            summary="Mock TTS available.",
            details={"default_voice": self.config.get("default_voice", "sweetie_mock_voice")},
        )


class MockAudioOutputPlugin(AudioOutputPlugin):
    @classmethod
    def manifest(cls) -> PluginManifest:
        return PluginManifest(
            plugin_id="sweetiebot.mock_audio_output",
            family=PluginFamily.AUDIO_OUTPUT,
            display_name="Mock Audio Output",
            description="Pretends to play audio for safe runtime testing.",
            capabilities=["play_audio", "report_playback_receipt"],
            priority=100,
        )

    def play(self, audio_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ok": True,
            "output": self.manifest().plugin_id,
            "accepted_format": audio_payload.get("audio_format"),
            "played_text": audio_payload.get("text", ""),
            "duration_ms": audio_payload.get("duration_ms", 0),
            "playback_mode": self.config.get("playback_mode", "silent"),
        }

    def healthcheck(self) -> PluginHealthCheck:
        return PluginHealthCheck(
            plugin_id=self.manifest().plugin_id,
            status=PluginHealthStatus.HEALTHY,
            summary="Mock audio output available.",
            details={"playback_mode": self.config.get("playback_mode", "silent")},
        )

from __future__ import annotations

from typing import Any, Dict, Optional

from sweetiebot.plugins.base import AudioOutputPlugin, TTSProviderPlugin
from sweetiebot.plugins.health import PluginHealthCheck, PluginHealthStatus
from sweetiebot.plugins.manifest import PluginManifest
from sweetiebot.plugins.types import PluginType


class MockTTSProviderPlugin(TTSProviderPlugin):
    plugin_id = "sweetiebot.mock_tts"

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self.plugin_id,
            plugin_type=PluginType.TTS_PROVIDER,
            display_name="Mock TTS Provider",
            description="Returns structured mock speech payloads for safe local testing.",
            capabilities=["synthesize_text", "mock_audio_payload"],
        )

    def synthesize(self, text: str, voice_profile: Optional[str] = None, voice: Optional[str] = None) -> Dict[str, Any]:
        cleaned = (text or "").strip()
        voice_name = voice_profile or voice or self.config.get("default_voice", "sweetie_mock_voice")
        return {
            "ok": True,
            "provider": self.manifest().plugin_id,
            "voice_profile": voice_name,
            "text": cleaned,
            "audio_format": "text/mock-audio",
            "audio_bytes": cleaned.encode("utf-8"),
            "duration_ms": max(250, min(len(cleaned) * 45, 8000)),
            "cached": False,
            "audio_ref": f"mock://audio/{len(cleaned)}",
            "voice": voice_name,
            "synthesized": True,
        }

    def healthcheck(self) -> PluginHealthCheck:
        return PluginHealthCheck(
            plugin_id=self.manifest().plugin_id,
            status=PluginHealthStatus.HEALTHY,
            summary="Mock TTS available.",
            details={"default_voice": self.config.get("default_voice", "sweetie_mock_voice")},
        )


class MockAudioOutputPlugin(AudioOutputPlugin):
    plugin_id = "sweetiebot.mock_audio_output"

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self.plugin_id,
            plugin_type=PluginType.AUDIO_OUTPUT,
            display_name="Mock Audio Output",
            description="Pretends to play audio for safe runtime testing.",
            capabilities=["play_audio", "report_playback_receipt"],
        )

    def play(self, audio_payload: Dict[str, Any] | str) -> Dict[str, Any]:
        if isinstance(audio_payload, str):
            audio_payload = {"audio_ref": audio_payload}
        return {
            "ok": True,
            "output": self.manifest().plugin_id,
            "accepted_format": audio_payload.get("audio_format"),
            "played_text": audio_payload.get("text", ""),
            "audio_ref": audio_payload.get("audio_ref"),
            "duration_ms": audio_payload.get("duration_ms", 0),
            "playback_mode": self.config.get("playback_mode", "silent"),
            "played": True,
        }

    def healthcheck(self) -> PluginHealthCheck:
        return PluginHealthCheck(
            plugin_id=self.manifest().plugin_id,
            status=PluginHealthStatus.HEALTHY,
            summary="Mock audio output available.",
            details={"playback_mode": self.config.get("playback_mode", "silent")},
        )

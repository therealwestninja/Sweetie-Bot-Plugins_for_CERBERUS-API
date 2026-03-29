from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from sweetiebot.plugins.base import AudioOutputPlugin, DialogueProviderPlugin, SafetyPolicyPlugin, TTSProviderPlugin
from sweetiebot.plugins.builtins import MockAudioOutputPlugin, MockTTSProviderPlugin
from sweetiebot.plugins.registry import PluginRegistry
from sweetiebot.plugins.types import PluginFamily


@dataclass
class RuntimeState:
    last_input: Optional[str] = None
    last_reply: Optional[Dict[str, Any]] = None
    last_speech: Optional[Dict[str, Any]] = None
    last_playback: Optional[Dict[str, Any]] = None
    degraded_mode: bool = False


class SweetieBotRuntime:
    def __init__(self, registry: Optional[PluginRegistry] = None) -> None:
        self.registry = registry or PluginRegistry()
        self.state = RuntimeState()
        self._register_builtins()

    def _register_builtins(self) -> None:
        existing_tts = self.registry.get_primary(PluginFamily.TTS_PROVIDER)
        existing_audio = self.registry.get_primary(PluginFamily.AUDIO_OUTPUT)
        if existing_tts is None:
            self.registry.register(MockTTSProviderPlugin())
        if existing_audio is None:
            self.registry.register(MockAudioOutputPlugin())

    def plugin_summary(self) -> Dict[str, Any]:
        return self.registry.summary()

    def plugin_health_summary(self) -> Dict[str, Any]:
        return self.registry.health_summary()

    def synthesize_speech(self, text: str, voice_profile: Optional[str] = None) -> Dict[str, Any]:
        plugin = self.registry.get_primary(PluginFamily.TTS_PROVIDER)
        if plugin is None:
            self.state.degraded_mode = True
            raise RuntimeError("No TTS provider plugin is registered.")
        payload = plugin.synthesize(text, voice_profile=voice_profile)
        self.state.last_speech = payload
        return payload

    def play_speech(self, speech_payload: Dict[str, Any]) -> Dict[str, Any]:
        plugin = self.registry.get_primary(PluginFamily.AUDIO_OUTPUT)
        if plugin is None:
            self.state.degraded_mode = True
            raise RuntimeError("No audio output plugin is registered.")
        receipt = plugin.play(speech_payload)
        self.state.last_playback = receipt
        return receipt

    def speak(self, text: str, voice_profile: Optional[str] = None) -> Dict[str, Any]:
        speech = self.synthesize_speech(text, voice_profile=voice_profile)
        playback = self.play_speech(speech)
        return {"speech": speech, "playback": playback}

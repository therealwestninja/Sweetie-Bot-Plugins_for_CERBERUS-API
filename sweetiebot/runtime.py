from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class RuntimeState:
    persona_id: str = "sweetie_bot"
    emote_id: str = "calm_neutral"
    routine_id: Optional[str] = None
    accessory_scene_id: Optional[str] = None
    safe_mode: bool = False
    degraded_mode: bool = False
    last_input: Optional[str] = None
    last_reply: Optional[Dict[str, Any]] = None
    last_speech: Optional[Dict[str, Any]] = None


class SweetieBotRuntime:
    """
    Minimal runtime patch showing health and safe speech hooks.
    Assumes a plugin registry object with helper methods exists in the main repo.
    """

    def __init__(self, plugin_registry: Any, dialogue_manager: Any = None) -> None:
        self.plugin_registry = plugin_registry
        self.dialogue_manager = dialogue_manager
        self.state = RuntimeState()

    def get_state(self) -> Dict[str, Any]:
        return asdict(self.state)

    def plugin_summary(self) -> Dict[str, Any]:
        if hasattr(self.plugin_registry, "health_summary"):
            return self.plugin_registry.health_summary()
        if hasattr(self.plugin_registry, "plugins"):
            from sweetiebot.plugins.health import summarize_plugin_health
            return summarize_plugin_health(self.plugin_registry.plugins())
        return {"ok": True, "counts": {"total": 0, "healthy": 0, "degraded": 0, "errors": 0}, "plugins": []}

    def speak(self, text: str, voice: Optional[str] = None) -> Dict[str, Any]:
        tts_plugin = None
        audio_plugin = None
        if hasattr(self.plugin_registry, "get_best_plugin"):
            tts_plugin = self.plugin_registry.get_best_plugin("tts_provider")
            audio_plugin = self.plugin_registry.get_best_plugin("audio_output")

        speech_result: Dict[str, Any] = {
            "text": text,
            "voice": voice or "default",
            "synthesized": False,
            "played": False,
            "audio_ref": None,
        }

        if tts_plugin is not None:
            speech_result.update(tts_plugin.synthesize(text=text, voice=voice))
        if audio_plugin is not None and speech_result.get("audio_ref"):
            play_result = audio_plugin.play(audio_ref=speech_result["audio_ref"])
            speech_result["played"] = bool(play_result.get("played", False))
            speech_result["playback"] = play_result

        self.state.last_speech = speech_result
        return speech_result

    def health(self) -> Dict[str, Any]:
        return {
            "runtime_ok": not self.state.degraded_mode,
            "safe_mode": self.state.safe_mode,
            "degraded_mode": self.state.degraded_mode,
            "plugins": self.plugin_summary(),
        }

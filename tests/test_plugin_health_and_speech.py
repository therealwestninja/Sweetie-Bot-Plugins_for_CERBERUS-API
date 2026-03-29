from sweetiebot.plugins.builtins import MockAudioOutputPlugin, MockTTSProviderPlugin
from sweetiebot.plugins.registry import PluginRegistry
from sweetiebot.plugins.types import PluginFamily
from sweetiebot.runtime import SweetieBotRuntime


def test_registry_health_summary_counts_plugins():
    registry = PluginRegistry()
    registry.register(MockTTSProviderPlugin())
    registry.register(MockAudioOutputPlugin())

    summary = registry.health_summary()

    assert summary["overall_status"] == "healthy"
    assert summary["counts"]["total"] == 2
    assert summary["counts"]["healthy"] == 2
    assert "tts_provider" in summary["families"]
    assert "audio_output" in summary["families"]


def test_mock_tts_provider_returns_structured_payload():
    plugin = MockTTSProviderPlugin({"default_voice": "sweetie_test"})
    payload = plugin.synthesize("Hello everypony!")

    assert payload["ok"] is True
    assert payload["provider"] == "sweetiebot.mock_tts"
    assert payload["voice_profile"] == "sweetie_test"
    assert payload["audio_format"] == "text/mock-audio"
    assert isinstance(payload["audio_bytes"], bytes)


def test_mock_audio_output_returns_receipt():
    plugin = MockAudioOutputPlugin({"playback_mode": "silent"})
    receipt = plugin.play({
        "audio_format": "text/mock-audio",
        "text": "Hello everypony!",
        "duration_ms": 400,
    })

    assert receipt["ok"] is True
    assert receipt["output"] == "sweetiebot.mock_audio_output"
    assert receipt["accepted_format"] == "text/mock-audio"
    assert receipt["playback_mode"] == "silent"


def test_runtime_speak_runs_mock_pipeline():
    runtime = SweetieBotRuntime()
    result = runtime.speak("Hi there!")

    assert result["speech"]["ok"] is True
    assert result["playback"]["ok"] is True
    assert runtime.state.last_speech["text"] == "Hi there!"
    assert runtime.state.last_playback["played_text"] == "Hi there!"

from sweetiebot.cli.main import run_cli
from sweetiebot.runtime import SweetieBotRuntime


class FakePluginType:
    def __init__(self, value: str) -> None:
        self.value = value


class FakeManifest:
    def __init__(self, plugin_id: str, plugin_type: str) -> None:
        self.plugin_id = plugin_id
        self.plugin_type = FakePluginType(plugin_type)
        self.version = "1.0.0"


class MockTTS:
    def manifest(self):
        return FakeManifest("sweetiebot.mock_tts", "tts_provider")

    def healthcheck(self):
        return {"ok": True, "status": "ok", "details": {"backend": "mock"}}

    def synthesize(self, text: str, voice=None):
        return {"synthesized": True, "audio_ref": "mock://audio/1", "voice": voice or "default", "text": text}


class MockAudio:
    def manifest(self):
        return FakeManifest("sweetiebot.mock_audio_output", "audio_output")

    def healthcheck(self):
        return {"ok": True, "status": "ok", "details": {"device": "default"}}

    def play(self, audio_ref: str):
        return {"played": True, "audio_ref": audio_ref}


class FakeRegistry:
    def __init__(self):
        self._plugins = [MockTTS(), MockAudio()]

    def plugins(self):
        return list(self._plugins)

    def get_best_plugin(self, plugin_type: str):
        for plugin in self._plugins:
            if plugin.manifest().plugin_type.value == plugin_type:
                return plugin
        return None


def test_cli_commands(capsys):
    runtime = SweetieBotRuntime(plugin_registry=FakeRegistry())

    assert run_cli(["plugin-health"], runtime) == 0
    out = capsys.readouterr().out
    assert "healthy" in out

    assert run_cli(["runtime-health"], runtime) == 0
    out = capsys.readouterr().out
    assert "runtime_ok" in out

    assert run_cli(["speak-test", "Hello"], runtime) == 0
    out = capsys.readouterr().out
    assert "synthesized" in out

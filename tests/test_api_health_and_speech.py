from fastapi.testclient import TestClient

from sweetiebot.api.app import create_app
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
        return {"synthesized": True, "audio_ref": f"mock://audio/{len(text)}", "voice": voice or "default", "text": text}


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


def make_runtime():
    return SweetieBotRuntime(plugin_registry=FakeRegistry())


def test_plugin_health_endpoint():
    app = create_app(make_runtime)
    client = TestClient(app)
    response = client.get("/character/health")
    assert response.status_code == 200
    data = response.json()
    assert data["plugins"]["counts"]["total"] == 2
    assert data["runtime_ok"] is True


def test_speak_test_endpoint():
    app = create_app(make_runtime)
    client = TestClient(app)
    response = client.post("/character/speak-test", json={"text": "Hello Sweetie Bot", "voice": "sweetie"})
    assert response.status_code == 200
    data = response.json()
    assert data["synthesized"] is True
    assert data["played"] is True
    assert data["voice"] == "sweetie"

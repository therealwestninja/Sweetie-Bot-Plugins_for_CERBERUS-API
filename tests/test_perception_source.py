from sweetiebot.plugins.builtins.perception import MockPerceptionSourcePlugin
from sweetiebot.runtime import SweetieBotRuntime


def test_mock_perception_source_returns_observations():
    plugin = MockPerceptionSourcePlugin()
    observations = plugin.poll_observations()
    assert observations
    assert observations[0].observation_type == "presence"


def test_runtime_poll_perception_records_observations():
    runtime = SweetieBotRuntime()
    items = runtime.poll_perception()
    assert items
    assert runtime.state["last_observations"]
    recalled = runtime.recall(kind="observation", limit=10)
    assert recalled


def test_runtime_apply_perception_updates_focus():
    runtime = SweetieBotRuntime()
    result = runtime.apply_perception()
    assert result["observations"]
    assert result["state"]["focus_target"] == "guest"

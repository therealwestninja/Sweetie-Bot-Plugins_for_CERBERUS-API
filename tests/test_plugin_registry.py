import pytest

from sweetiebot.plugins import PluginError, PluginRegistry, PluginType
from sweetiebot.plugins.builtins import DemoRoutinePackPlugin, LocalDialogueProviderPlugin


def test_plugin_registry_registers_builtins_and_sorts_by_priority() -> None:
    registry = PluginRegistry()
    registry.register_builtins()
    assert registry.list_ids_for_type(PluginType.DIALOGUE_PROVIDER) == [
        "sweetiebot.local_dialogue"
    ]
    assert registry.list_ids_for_type(PluginType.ROUTINE_PACK) == ["sweetiebot.demo_routines"]


def test_plugin_registry_rejects_duplicates() -> None:
    registry = PluginRegistry()
    registry.register(LocalDialogueProviderPlugin())
    with pytest.raises(PluginError):
        registry.register(LocalDialogueProviderPlugin())


def test_plugin_registry_runs_dialogue_plugin() -> None:
    registry = PluginRegistry()
    registry.register_builtins()
    payload = registry.run_dialogue(user_text="hello", runtime_context={})
    assert payload["intent"] == "greet"
    assert payload["directive"]["routine_id"] == "greet_guest"


def test_demo_routine_pack_exposes_expected_routines() -> None:
    plugin = DemoRoutinePackPlugin()
    routines = plugin.list_routines()
    assert set(routines) >= {"greet_guest", "photo_pose", "idle_cute", "return_to_neutral"}

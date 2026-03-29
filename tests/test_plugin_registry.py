from pathlib import Path

import pytest

from sweetiebot.plugins import PluginConfigError, PluginError, PluginRegistry, PluginType, load_plugin_config
from sweetiebot.plugins.builtins import DemoRoutinePackPlugin, LocalDialogueProviderPlugin


def test_plugin_registry_registers_builtins_and_sorts_by_priority() -> None:
    registry = PluginRegistry()
    registry.register_builtins()
    assert registry.list_ids_for_type(PluginType.SAFETY_POLICY) == [
        "sweetiebot.default_safety_policy"
    ]
    # Both dialogue providers are registered.
    # Local(priority=10) sorts before Structured(priority=20) so get_best_plugin
    # returns LocalDialogueProviderPlugin — preserving the legacy run_dialogue path.
    dialogue_ids = registry.list_ids_for_type(PluginType.DIALOGUE_PROVIDER)
    assert "sweetiebot.local_dialogue" in dialogue_ids
    assert "sweetiebot.dialogue.structured" in dialogue_ids
    # Local (priority 10) wins over Structured (priority 20)
    assert dialogue_ids[0] == "sweetiebot.local_dialogue"
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


def test_plugin_config_loader_reads_yaml(tmp_path: Path) -> None:
    path = tmp_path / "plugins.yaml"
    path.write_text(
        """
plugins:
  sweetiebot.default_safety_policy:
    max_spoken_chars: 40
    blocked_terms:
      - contraband
""".strip(),
        encoding="utf-8",
    )
    payload = load_plugin_config(path)
    assert payload["sweetiebot.default_safety_policy"]["max_spoken_chars"] == 40


def test_plugin_config_loader_rejects_non_mapping(tmp_path: Path) -> None:
    path = tmp_path / "plugins.yaml"
    path.write_text("- nope\n", encoding="utf-8")
    with pytest.raises(PluginConfigError):
        load_plugin_config(path)

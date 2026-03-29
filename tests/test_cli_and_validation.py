from __future__ import annotations

import json

import yaml

from sweetiebot.cli.main import build_parser
from sweetiebot.persona.loader import load_persona_file
from sweetiebot.plugins.registry import PluginRegistry
from sweetiebot.routines.registry import load_routines_file
from sweetiebot.runtime import SweetieBotRuntime


def test_plugin_registry_lists_builtins():
    registry = PluginRegistry()
    plugins = registry.list_plugins()
    assert any(item["plugin_id"] == "sweetiebot.local_dialogue_provider" for item in plugins)


def test_load_persona_file(tmp_path):
    path = tmp_path / "persona.yaml"
    path.write_text(yaml.safe_dump({"persona_id": "sweetie", "display_name": "Sweetie Bot"}), encoding="utf-8")
    persona = load_persona_file(path)
    assert persona.display_name == "Sweetie Bot"


def test_load_routines_file(tmp_path):
    path = tmp_path / "routines.yaml"
    path.write_text(yaml.safe_dump({"routines": [{"routine_id": "wave", "steps": [{"action": "emote", "value": "happy"}]}]}), encoding="utf-8")
    routines = load_routines_file(path)
    assert routines[0].routine_id == "wave"


def test_runtime_say_and_clip():
    runtime = SweetieBotRuntime()
    runtime.plugins.configure_from_mapping({"plugins": {"sweetiebot.default_safety_policy": {"max_spoken_chars": 12}}})
    reply = runtime.say("This input triggers a longer local echo response than normal.")
    assert len(reply.spoken_text) <= 12


def test_cli_parser_builds():
    parser = build_parser()
    args = parser.parse_args(["test-dialogue", "hello"])
    assert args.text == "hello"

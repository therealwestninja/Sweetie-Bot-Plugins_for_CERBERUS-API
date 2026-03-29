from __future__ import annotations

import argparse
import json
from pathlib import Path

from sweetiebot.persona.loader import load_persona_file
from sweetiebot.plugins.registry import PluginRegistry
from sweetiebot.routines.registry import load_routines_file
from sweetiebot.runtime import SweetieBotRuntime


def _cmd_list_plugins(_args: argparse.Namespace) -> int:
    registry = PluginRegistry()
    print(json.dumps(registry.list_plugins(), indent=2))
    return 0


def _cmd_validate_persona(args: argparse.Namespace) -> int:
    persona = load_persona_file(args.path)
    print(json.dumps(persona.model_dump(), indent=2))
    return 0


def _cmd_validate_routines(args: argparse.Namespace) -> int:
    routines = load_routines_file(args.path)
    print(json.dumps([item.model_dump() for item in routines], indent=2))
    return 0


def _cmd_test_dialogue(args: argparse.Namespace) -> int:
    runtime = SweetieBotRuntime()
    if args.config:
        runtime.plugins.configure_from_yaml(Path(args.config).read_text(encoding="utf-8"))
    reply = runtime.say(args.text)
    print(json.dumps(reply.model_dump(), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sweetiebot", description="Sweetie Bot utility CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_plugins = subparsers.add_parser("list-plugins", help="List all registered plugins")
    list_plugins.set_defaults(func=_cmd_list_plugins)

    validate_persona = subparsers.add_parser("validate-persona", help="Validate a persona YAML file")
    validate_persona.add_argument("path")
    validate_persona.set_defaults(func=_cmd_validate_persona)

    validate_routines = subparsers.add_parser("validate-routines", help="Validate a routines YAML file")
    validate_routines.add_argument("path")
    validate_routines.set_defaults(func=_cmd_validate_routines)

    test_dialogue = subparsers.add_parser("test-dialogue", help="Generate a test dialogue reply")
    test_dialogue.add_argument("text")
    test_dialogue.add_argument("--config", help="Optional plugin configuration YAML file")
    test_dialogue.set_defaults(func=_cmd_test_dialogue)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

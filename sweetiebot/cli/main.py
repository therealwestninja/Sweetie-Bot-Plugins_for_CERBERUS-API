from __future__ import annotations

import argparse
import json
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sweetiebot")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-plugins", help="List registered plugins")
    sub.add_parser("plugin-health", help="Show plugin health summary")
    sub.add_parser("runtime-health", help="Show runtime health summary")

    speak = sub.add_parser("speak-test", help="Run safe speech synthesis/playback test")
    speak.add_argument("text")
    speak.add_argument("--voice", default=None)

    return parser


def run_cli(argv: list[str], runtime: Any) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list-plugins":
        if hasattr(runtime.plugin_registry, "plugins"):
            payload = []
            for plugin in runtime.plugin_registry.plugins():
                manifest = plugin.manifest()
                payload.append(
                    {
                        "plugin_id": manifest.plugin_id,
                        "plugin_type": getattr(manifest.plugin_type, "value", str(manifest.plugin_type)),
                        "version": manifest.version,
                    }
                )
            print(json.dumps(payload, indent=2))
            return 0
        print("[]")
        return 0

    if args.command == "plugin-health":
        print(json.dumps(runtime.plugin_summary(), indent=2))
        return 0

    if args.command == "runtime-health":
        print(json.dumps(runtime.health(), indent=2))
        return 0

    if args.command == "speak-test":
        print(json.dumps(runtime.speak(text=args.text, voice=args.voice), indent=2))
        return 0

    parser.print_help()
    return 1

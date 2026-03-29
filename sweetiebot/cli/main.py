from __future__ import annotations

import argparse
import json
from typing import Sequence

from sweetiebot.runtime import SweetieBotRuntime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sweetiebot")
    sub = parser.add_subparsers(dest="command")

    td = sub.add_parser("test-dialogue")
    td.add_argument("text")

    sp = sub.add_parser("speak")
    sp.add_argument("text")

    st = sub.add_parser("speak-test")
    st.add_argument("text")

    sub.add_parser("health")
    sub.add_parser("plugin-health")
    sub.add_parser("runtime-health")
    return parser


def run_cli(argv: Sequence[str] | None = None, runtime_factory=SweetieBotRuntime) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    runtime = runtime_factory() if callable(runtime_factory) else runtime_factory
    if args.command == "test-dialogue":
        print(json.dumps(runtime.say(args.text).to_dict() if hasattr(runtime.say(args.text), "to_dict") else runtime.say(args.text)))
        return 0
    if args.command in {"speak", "speak-test"}:
        result = runtime.speak(args.text)
        print(json.dumps(result.to_dict() if hasattr(result, "to_dict") else result))
        return 0
    if args.command in {"health", "runtime-health"}:
        payload = {"runtime_ok": True}
        print(json.dumps(payload))
        return 0
    if args.command == "plugin-health":
        if hasattr(runtime.plugins, "health_summary"):
            payload = runtime.plugins.health_summary()
        else:
            from sweetiebot.plugins.health import summarize_plugin_health
            payload = summarize_plugin_health(runtime.plugins.plugins()) if hasattr(runtime.plugins, "plugins") else {"overall_status": "unknown"}
        print(json.dumps(payload))
        return 0
    parser.print_help()
    return 0


def main() -> None:
    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()

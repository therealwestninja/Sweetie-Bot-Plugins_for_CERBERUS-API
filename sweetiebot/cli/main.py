from __future__ import annotations

import argparse
import json

from sweetiebot.runtime import SweetieBotRuntime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sweetiebot")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("runtime-health")
    sub.add_parser("state-show")

    state_update = sub.add_parser("state-update")
    state_update.add_argument("--mood")
    state_update.add_argument("--focus-target")
    state_update.add_argument("--active-routine")
    state_update.add_argument("--active-emote")
    state_update.add_argument("--accessory-scene")
    state_update.add_argument("--safe-mode", choices=["true", "false"])
    state_update.add_argument("--degraded-mode", choices=["true", "false"])

    remember = sub.add_parser("remember")
    remember.add_argument("--kind", required=True)
    remember.add_argument("--content", required=True)
    remember.add_argument("--source", default="cli")
    remember.add_argument("--scope", default="session")

    recent = sub.add_parser("memory-recent")
    recent.add_argument("--limit", type=int, default=10)

    search = sub.add_parser("memory-search")
    search.add_argument("--text")
    search.add_argument("--kind")
    search.add_argument("--scope")
    search.add_argument("--limit", type=int, default=10)

    return parser


def _parse_bool(value):
    if value is None:
        return None
    return value.lower() == "true"


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    runtime = SweetieBotRuntime()

    if args.command == "runtime-health":
        print(json.dumps(runtime.runtime_health(), indent=2))
        return 0

    if args.command == "state-show":
        print(json.dumps(runtime.character_state(), indent=2))
        return 0

    if args.command == "state-update":
        result = runtime.update_character_state(
            mood=args.mood,
            focus_target=args.focus_target,
            active_routine=args.active_routine,
            active_emote=args.active_emote,
            accessory_scene=args.accessory_scene,
            safe_mode=_parse_bool(args.safe_mode),
            degraded_mode=_parse_bool(args.degraded_mode),
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "remember":
        result = runtime.remember(args.kind, args.content, source=args.source, scope=args.scope)
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "memory-recent":
        print(json.dumps({"items": runtime.recall(limit=args.limit)}, indent=2))
        return 0

    if args.command == "memory-search":
        print(json.dumps({
            "items": runtime.recall(
                text=args.text,
                kind=args.kind,
                scope=args.scope,
                limit=args.limit,
            )
        }, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

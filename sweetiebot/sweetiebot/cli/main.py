from __future__ import annotations

import argparse
import json

from sweetiebot.runtime import SweetieBotRuntime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sweetiebot")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("runtime-health")
    sub.add_parser("state-show")
    sub.add_parser("dialogue-show")
    sub.add_parser("emote-show")
    sub.add_parser("mood-show")
    sub.add_parser("perception-show")
    sub.add_parser("attention-show")
    sub.add_parser("behavior-show")
    sub.add_parser("routine-arbitration-show")
    sub.add_parser("telemetry-show")
    sub.add_parser("perception-poll")
    sub.add_parser("perception-apply")

    dialogue_generate = sub.add_parser("dialogue-generate")
    dialogue_generate.add_argument("--text")

    emote_map = sub.add_parser("emote-map")
    emote_map.add_argument("--dialogue-intent")
    emote_map.add_argument("--suggested-emote-id")
    emote_map.add_argument("--behavior-action")

    telemetry_events = sub.add_parser("telemetry-events")
    telemetry_events.add_argument("--limit", type=int, default=25)

    attention_suggest = sub.add_parser("attention-suggest")
    attention_suggest.add_argument("--text")

    attention_apply = sub.add_parser("attention-apply")
    attention_apply.add_argument("--text")

    behavior_suggest = sub.add_parser("behavior-suggest")
    behavior_suggest.add_argument("--text")

    behavior_arbitrate = sub.add_parser("behavior-arbitrate")
    behavior_arbitrate.add_argument("--text")

    routine_arbitrate = sub.add_parser("routine-arbitrate")
    routine_arbitrate.add_argument("--routine")

    mood_event = sub.add_parser("mood-event")
    mood_event.add_argument("--event", required=True)

    sub.add_parser("mood-decay")

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

    if args.command == "dialogue-show":
        print(json.dumps(runtime.dialogue_status(), indent=2))
        return 0

    if args.command == "dialogue-generate":
        print(json.dumps(runtime.generate_dialogue(user_text=args.text), indent=2))
        return 0

    if args.command == "emote-show":
        print(json.dumps(runtime.emote_status(), indent=2))
        return 0

    if args.command == "emote-map":
        print(json.dumps(runtime.map_emote(
            dialogue_intent=args.dialogue_intent,
            suggested_emote_id=args.suggested_emote_id,
            behavior_action=args.behavior_action,
        ), indent=2))
        return 0

    if args.command == "mood-show":
        print(json.dumps(runtime.mood_status(), indent=2))
        return 0

    if args.command == "perception-show":
        print(json.dumps(runtime.perception_status(), indent=2))
        return 0

    if args.command == "perception-poll":
        print(json.dumps({"items": runtime.poll_perception()}, indent=2))
        return 0

    if args.command == "perception-apply":
        print(json.dumps(runtime.apply_perception(), indent=2))
        return 0

    if args.command == "attention-show":
        print(json.dumps(runtime.attention_status(), indent=2))
        return 0

    if args.command == "behavior-show":
        print(json.dumps(runtime.behavior_status(), indent=2))
        return 0

    if args.command == "routine-arbitration-show":
        print(json.dumps(runtime.routine_arbitrator.snapshot(), indent=2))
        return 0

    if args.command == "telemetry-show":
        print(json.dumps(runtime.telemetry_status(), indent=2))
        return 0

    if args.command == "telemetry-events":
        print(json.dumps({"items": runtime.recent_trace_events(limit=args.limit)}, indent=2))
        return 0

    if args.command == "attention-suggest":
        print(json.dumps(runtime.suggest_attention(user_text=args.text), indent=2))
        return 0

    if args.command == "attention-apply":
        print(json.dumps(runtime.apply_attention(user_text=args.text), indent=2))
        return 0

    if args.command == "behavior-suggest":
        print(json.dumps(runtime.suggest_behavior(user_text=args.text), indent=2))
        return 0

    if args.command == "behavior-arbitrate":
        print(json.dumps(runtime.suggest_and_arbitrate_behavior(user_text=args.text), indent=2))
        return 0

    if args.command == "routine-arbitrate":
        print(json.dumps(runtime.arbitrate_routine(args.routine), indent=2))
        return 0

    if args.command == "mood-event":
        print(json.dumps(runtime.apply_mood_event(args.event), indent=2))
        return 0

    if args.command == "mood-decay":
        print(json.dumps(runtime.decay_mood(), indent=2))
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

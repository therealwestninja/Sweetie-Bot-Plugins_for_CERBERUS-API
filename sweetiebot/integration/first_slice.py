
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


SCHEMA_VERSION = "1.0"


def make_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    source: str,
    replay_safe: bool = False,
) -> dict[str, Any]:
    """Canonical websocket event envelope for the first real integration slice."""
    return {
        "type": event_type,
        "source": source,
        "schema_version": SCHEMA_VERSION,
        "replay_safe": replay_safe,
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "payload": payload,
    }


def make_snapshot_payload(
    *,
    bridge: Any,
    gate: Any,
    mapper: Any,
    ledger: Any,
) -> dict[str, Any]:
    """Build the replay-safe snapshot payload sent to every websocket client."""
    return {
        **bridge.snapshot_payload(),
        "safety_mode": getattr(getattr(gate, "safety_mode", None), "value", "normal"),
        "gate": gate.snapshot() if hasattr(gate, "snapshot") else {},
        "mapper": mapper.snapshot() if hasattr(mapper, "snapshot") else {},
        "recent_decisions": ledger.recent(limit=5) if hasattr(ledger, "recent") else [],
    }


def normalize_nudge_request(raw: Any) -> dict[str, Any]:
    """
    Accept both the repo's current request shape and the proposed UI request shape.

    Supported examples:
      {"nudge_type": "attention", "source": "companion_web", "note": ""}
      {"intent": "greet", "context": {"target": "guest"}}
    """
    if hasattr(raw, "model_dump"):
        raw = raw.model_dump()

    raw = dict(raw or {})
    intent = raw.get("intent") or raw.get("nudge_type") or "idle"
    context = raw.get("context") or {}
    return {
        "intent": str(intent),
        "source": str(raw.get("source") or "companion_web"),
        "note": str(raw.get("note") or ""),
        "context": context if isinstance(context, dict) else {},
    }


def reaction_for_intent(intent: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    target = context.get("target") or "guest"

    if intent == "greet":
        return {
            "speech": "Oh! Hello there~!",
            "emote": "warm_smile",
            "attention": target,
            "intensity": 0.85,
        }
    if intent == "perk_up":
        return {
            "speech": "",
            "emote": "curious_headtilt",
            "attention": "forward",
            "intensity": 0.65,
        }
    if intent == "focus":
        return {
            "speech": "",
            "emote": "curious_headtilt",
            "attention": target,
            "intensity": 0.70,
        }
    if intent == "idle":
        return {
            "speech": "",
            "emote": "eyes_neutral",
            "attention": "none",
            "intensity": 0.20,
        }

    return {
        "speech": "",
        "emote": "warm_smile",
        "attention": "forward",
        "intensity": 0.35,
    }


def decision_for_intent(intent: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    action_type = {
        "greet": "routine",
        "perk_up": "emote",
        "focus": "focus",
        "idle": "accessory_scene",
    }.get(intent, "emote")

    action_id = {
        "greet": "greet_guest",
        "perk_up": "curious_headtilt",
        "focus": "look_at_target",
        "idle": "eyes_neutral",
    }.get(intent, intent)

    return {
        "action_type": action_type,
        "action_id": action_id,
        "parameters": context,
        "source_event_id": str(uuid4()),
        "safety_mode": "normal",
    }


def adapt_nudge_response(
    *,
    raw: Any,
    bridge: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Convert an incoming nudge into a stable reaction/decision pair."""
    normalized = normalize_nudge_request(raw)
    reaction = reaction_for_intent(normalized["intent"], normalized["context"])
    decision = decision_for_intent(normalized["intent"], normalized["context"])
    payload = {
        "nudge_type": normalized["intent"],
        "reaction": reaction,
        "decision": decision,
        "character": bridge.character_payload(),
    }
    return normalized, payload


async def publish_canonical_nudge_event(*, events: Any, payload: dict[str, Any]) -> None:
    """Publish the canonical character.nudge_reaction event."""
    if hasattr(events, "publish"):
        envelope = make_event(
            "character.nudge_reaction",
            payload,
            source="sweetiebot_nudge",
        )
        try:
            # Supports the current EventHub.publish(EventEnvelope(...)) approach
            from sweetiebot.api.app import EventEnvelope  # local import to avoid cycles at module import time

            await events.publish(
                EventEnvelope(
                    event_type=envelope["type"],
                    source=envelope["source"],
                    payload={
                        **envelope["payload"],
                        "schema_version": envelope["schema_version"],
                        "replay_safe": envelope["replay_safe"],
                    },
                )
            )
            return
        except Exception:
            # Fallback for alternate event bus shapes
            await events.publish(envelope)


async def publish_canonical_ack_event(*, events: Any, payload: dict[str, Any]) -> None:
    if hasattr(events, "publish"):
        envelope = make_event(
            "cerberus.execution_ack",
            payload,
            source="cerberus",
        )
        try:
            from sweetiebot.api.app import EventEnvelope

            await events.publish(
                EventEnvelope(
                    event_type=envelope["type"],
                    source=envelope["source"],
                    payload={
                        **envelope["payload"],
                        "schema_version": envelope["schema_version"],
                        "replay_safe": envelope["replay_safe"],
                    },
                )
            )
            return
        except Exception:
            await events.publish(envelope)


async def run_cerberus_stub(*, events: Any, decision: dict[str, Any]) -> dict[str, Any]:
    """
    A deliberately tiny, safe execution stub.
    Replace this with a real CERBERUS transport once hardware mapping is ready.
    """
    await asyncio.sleep(0.05)
    ack = {
        "status": "ok",
        "action_id": decision["action_id"],
        "action_type": decision["action_type"],
        "message": "stub-executed",
        "source_event_id": decision["source_event_id"],
    }
    await publish_canonical_ack_event(events=events, payload=ack)
    return ack

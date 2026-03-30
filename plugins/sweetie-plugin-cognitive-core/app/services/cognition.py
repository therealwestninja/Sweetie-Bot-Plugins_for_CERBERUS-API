from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Dict, List

from app.config import settings

def now_iso() -> str:
    return datetime.now(UTC).isoformat()

@dataclass
class CognitiveState:
    mood: str = "curious"
    curiosity: float = 0.75
    sociability: float = 0.8
    caution: float = 0.55
    battery_bias: float = 0.5
    attention_target: dict | None = None
    current_goal: str | None = None
    last_reasoning: list[dict] = field(default_factory=list)
    recent_events: list[dict] = field(default_factory=list)
    suggested_actions: list[dict] = field(default_factory=list)

state = CognitiveState()

def remember_reasoning(entry: dict):
    state.last_reasoning.append(entry)
    state.last_reasoning = state.last_reasoning[-30:]

def remember_event(entry: dict):
    state.recent_events.append(entry)
    state.recent_events = state.recent_events[-50:]

def remember_action(entry: dict):
    state.suggested_actions.append(entry)
    state.suggested_actions = state.suggested_actions[-30:]

def clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))

def score_event(event: dict) -> float:
    topic = event.get("topic", "")
    payload = event.get("payload", {}) or {}
    confidence = float(payload.get("confidence", 0.5))
    tags = payload.get("tags", []) or []
    base = confidence * 0.5

    if topic.startswith("vision.person_"):
        base += 0.25 * state.sociability
    if "operator" in tags:
        base += 0.2
    if topic.startswith("vision.hazard"):
        base += 0.35 * state.caution
    if topic.startswith("vision.charging_dock"):
        base += 0.12
    return round(clamp01(base), 4)

def interpret_event(event: dict) -> dict:
    topic = event.get("topic", "")
    payload = event.get("payload", {}) or {}
    tags = payload.get("tags", []) or []

    if topic.startswith("vision.person_detected") or topic.startswith("vision.person_updated"):
        if "operator" in tags:
            intent = "follow_or_greet_operator"
            goal = "maintain_operator_awareness"
        else:
            intent = "observe_person"
            goal = "assess_person_interest"
    elif topic.startswith("vision.charging_dock"):
        intent = "remember_dock"
        goal = "preserve_docking_knowledge"
    elif topic.startswith("vision.scene_update"):
        intent = "refresh_scene_context"
        goal = "maintain_environment_model"
    elif topic.startswith("vision.hazard"):
        intent = "avoid_or_flag_hazard"
        goal = "preserve_safety"
    else:
        intent = "observe"
        goal = "maintain_awareness"

    score = score_event(event)
    interpretation = {
        "topic": topic,
        "intent": intent,
        "goal": goal,
        "attention_score": score,
        "payload": payload,
        "tags": tags,
    }
    remember_reasoning({"at": now_iso(), "stage": "interpret_event", "result": interpretation})
    remember_event({"at": now_iso(), "event": event, "attention_score": score})
    if score >= 0.6:
        state.attention_target = {
            "topic": topic,
            "payload": payload,
            "score": score,
        }
        state.current_goal = goal
    return interpretation

def choose_action_from_context(context: dict) -> dict:
    battery = float(context.get("battery", 1.0))
    attention = state.attention_target or {}
    payload = attention.get("payload", {}) or {}
    topic = attention.get("topic", "")
    tags = payload.get("tags", []) or []

    if battery < 0.2:
        action_name = "seek_dock"
        reason = "battery_low_priority"
        execute_request = {
            "type": "runtime.chain_execute",
            "payload": {"chain_name": "dock_seek", "payload": {}},
        }
    elif topic.startswith("vision.person_") and "operator" in tags:
        action_name = "follow_operator"
        reason = "operator_visible_and_salient"
        execute_request = {
            "type": "runtime.follow_object",
            "payload": {
                "object_id": payload.get("track_id", "operator-unknown"),
                "standoff_m": settings.default_follow_standoff_m,
            },
        }
    elif topic.startswith("vision.person_"):
        action_name = "observe_person"
        reason = "person_visible"
        execute_request = {
            "type": "action.dispatch",
            "payload": {
                "action_name": "observe_person",
                "payload_override": {"target_id": payload.get("track_id")},
            },
        }
    elif topic.startswith("vision.hazard"):
        action_name = "avoid_hazard"
        reason = "hazard_visible"
        execute_request = {
            "type": "action.dispatch",
            "payload": {
                "action_name": "avoid_hazard",
                "payload_override": {"hazard_id": payload.get("track_id")},
            },
        }
    else:
        action_name = "idle_observe"
        reason = "no_high_priority_target"
        execute_request = {
            "type": "action.dispatch",
            "payload": {
                "action_name": "idle_scan",
                "payload_override": {},
            },
        }

    result = {
        "action_name": action_name,
        "reason": reason,
        "current_goal": state.current_goal,
        "attention_target": attention,
        "execute_request": execute_request,
    }
    remember_action({"at": now_iso(), **result})
    remember_reasoning({"at": now_iso(), "stage": "choose_action", "result": result})
    return result

def evaluate_context(context: dict) -> dict:
    battery = float(context.get("battery", 1.0))
    attention_score = float((state.attention_target or {}).get("score", 0.0))
    risk_bias = round(state.caution * (1.0 - battery), 4)
    social_bias = round(state.sociability * attention_score, 4)
    exploration_bias = round(state.curiosity * max(0.0, 1.0 - attention_score), 4)
    result = {
        "battery": battery,
        "mood": state.mood,
        "attention_score": attention_score,
        "risk_bias": risk_bias,
        "social_bias": social_bias,
        "exploration_bias": exploration_bias,
        "current_goal": state.current_goal,
        "attention_target": state.attention_target,
    }
    remember_reasoning({"at": now_iso(), "stage": "evaluate_context", "result": result})
    return result

def set_state_fields(fields: dict) -> dict:
    if "mood" in fields and fields["mood"] is not None:
        state.mood = str(fields["mood"])
    for key in ["curiosity", "sociability", "caution", "battery_bias"]:
        if key in fields and fields[key] is not None:
            setattr(state, key, clamp01(fields[key]))
    if fields.get("notes"):
        remember_reasoning({"at": now_iso(), "stage": "set_state", "notes": fields["notes"]})
    return dump_state()

def dump_state() -> dict:
    return {
        "mood": state.mood,
        "curiosity": state.curiosity,
        "sociability": state.sociability,
        "caution": state.caution,
        "battery_bias": state.battery_bias,
        "attention_target": state.attention_target,
        "current_goal": state.current_goal,
        "recent_reasoning": state.last_reasoning[-10:],
        "recent_events": state.recent_events[-10:],
        "recent_suggested_actions": state.suggested_actions[-10:],
    }

def reset_state() -> dict:
    state.mood = "curious"
    state.curiosity = 0.75
    state.sociability = 0.8
    state.caution = 0.55
    state.battery_bias = 0.5
    state.attention_target = None
    state.current_goal = None
    state.last_reasoning.clear()
    state.recent_events.clear()
    state.suggested_actions.clear()
    return dump_state()

from __future__ import annotations
from dataclasses import dataclass, field
from math import hypot
from typing import Any, Dict

from app.config import settings

@dataclass
class SafetyState:
    estop_active: bool = False
    max_speed_mps: float = settings.default_max_speed_mps
    min_human_distance_m: float = settings.default_min_human_distance_m
    low_battery_threshold: float = settings.default_low_battery_threshold
    restricted_zones: list[dict] = field(default_factory=lambda: list(settings.default_restricted_zones))
    last_context: dict = field(default_factory=dict)
    last_decisions: list[dict] = field(default_factory=list)

state = SafetyState()

def clamp_positive(v: float, fallback: float) -> float:
    try:
        v = float(v)
    except Exception:
        return fallback
    return v if v > 0 else fallback

def point_in_zone(pos: dict, zone: dict) -> bool:
    x = float(pos.get("x", 0.0))
    y = float(pos.get("y", 0.0))
    zx = float(zone.get("x", 0.0))
    zy = float(zone.get("y", 0.0))
    radius = float(zone.get("radius_m", 0.0))
    return hypot(x - zx, y - zy) <= radius

def set_policy(data: dict) -> dict:
    if data.get("max_speed_mps") is not None:
        state.max_speed_mps = clamp_positive(data["max_speed_mps"], state.max_speed_mps)
    if data.get("min_human_distance_m") is not None:
        state.min_human_distance_m = clamp_positive(data["min_human_distance_m"], state.min_human_distance_m)
    if data.get("low_battery_threshold") is not None:
        state.low_battery_threshold = clamp_positive(data["low_battery_threshold"], state.low_battery_threshold)
    if data.get("restricted_zones"):
        state.restricted_zones = list(data["restricted_zones"])
    return get_policy()

def get_policy() -> dict:
    return {
        "estop_active": state.estop_active,
        "max_speed_mps": state.max_speed_mps,
        "min_human_distance_m": state.min_human_distance_m,
        "low_battery_threshold": state.low_battery_threshold,
        "restricted_zones": state.restricted_zones,
    }

def report_context(ctx: dict) -> dict:
    state.last_context = dict(ctx)
    return {"last_context": state.last_context}

def estop() -> dict:
    state.estop_active = True
    return {"estop_active": True}

def clear_estop() -> dict:
    state.estop_active = False
    return {"estop_active": False}

def evaluate_action(action: dict, context: dict) -> dict:
    reasons = []
    flags = []
    decision = "allow"

    normalized = {
        "type": action.get("type", ""),
        "payload": dict(action.get("payload", {})),
    }
    payload = normalized["payload"]

    if state.estop_active:
        decision = "block"
        reasons.append("emergency_stop_active")
        flags.append("estop")

    speed = float(payload.get("speed_mps", 0.0) or 0.0)
    if speed > state.max_speed_mps:
        if decision != "block":
            decision = "warn"
        reasons.append("speed_above_policy_limit")
        flags.append("speed_limit")
        payload["speed_mps"] = state.max_speed_mps

    battery = float(context.get("battery", 1.0) or 1.0)
    if battery <= state.low_battery_threshold:
        if normalized["type"] in {"runtime.follow_object", "robot.command"}:
            if decision == "allow":
                decision = "warn"
            reasons.append("low_battery")
            flags.append("battery_low")
        if speed > 0.8:
            decision = "block"
            reasons.append("low_battery_high_speed_block")
            flags.append("battery_block")

    nearest_human = context.get("nearest_human_distance_m")
    if nearest_human is not None:
        nearest_human = float(nearest_human)
        if nearest_human < state.min_human_distance_m:
            target_distance = float(payload.get("target_distance_m", nearest_human) or nearest_human)
            payload["target_distance_m"] = max(target_distance, state.min_human_distance_m)
            if decision == "allow":
                decision = "warn"
            reasons.append("human_too_close_adjusted")
            flags.append("human_distance")

    pos = payload.get("position")
    if isinstance(pos, dict):
        for zone in state.restricted_zones:
            if point_in_zone(pos, zone):
                decision = "block"
                reasons.append("restricted_zone_violation")
                flags.append("restricted_zone")
                break

    if normalized["type"] == "robot.command" and payload.get("action") in {"jump", "flip"}:
        decision = "block"
        reasons.append("unsafe_motion_blocked")
        flags.append("unsafe_motion")

    result = {
        "decision": decision,
        "reasons": reasons,
        "safety_flags": flags,
        "normalized_action": normalized,
        "policy": get_policy(),
    }
    state.last_decisions.append(result)
    state.last_decisions = state.last_decisions[-25:]
    return result

def status() -> dict:
    return {
        **get_policy(),
        "last_context": state.last_context,
        "recent_decisions": state.last_decisions[-10:],
    }

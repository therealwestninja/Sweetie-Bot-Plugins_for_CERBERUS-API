from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC
from math import hypot

from app.config import settings

def now_iso() -> str:
    return datetime.now(UTC).isoformat()

def distance(a: dict, b: dict) -> float:
    return hypot(b["x"] - a["x"], b["y"] - a["y"])

@dataclass
class DockingState:
    dock_name: str = "charging_dock"
    dock_position: dict | None = None
    mode: str = "idle"
    charging: bool = False
    last_plan: dict | None = None
    history: list[dict] = field(default_factory=list)

state = DockingState()

def remember(entry: dict):
    state.history.append({"at": now_iso(), **entry})
    state.history = state.history[-25:]

def set_dock(dock_name: str, position: dict) -> dict:
    state.dock_name = dock_name
    state.dock_position = {"x": float(position["x"]), "y": float(position["y"])}
    remember({"event": "set_dock", "dock_name": dock_name, "dock_position": state.dock_position})
    return {"dock_name": state.dock_name, "dock_position": state.dock_position}

def seek_dock(battery: float, current_position: dict) -> dict:
    if not state.dock_position:
        result = {
            "should_dock": False,
            "reason": "dock_unknown",
            "suggested_action": None,
        }
        remember({"event": "seek_dock", **result})
        return result

    should_dock = battery <= settings.low_battery_threshold
    reason = "battery_low" if should_dock else "battery_ok"
    state.mode = "seeking" if should_dock else "idle"

    suggested = None
    if should_dock:
        suggested = {
            "type": "navigation.plan_to_point",
            "payload": {"goal": dict(state.dock_position)},
        }

    result = {
        "should_dock": should_dock,
        "reason": reason,
        "dock_target": dict(state.dock_position),
        "distance_to_dock_m": round(distance(current_position, state.dock_position), 4),
        "suggested_action": suggested,
    }
    remember({"event": "seek_dock", **result})
    return result

def plan_approach(current_position: dict, dock_position: dict | None = None) -> dict:
    dock = dock_position or state.dock_position
    if not dock:
        return {"planned": False, "reason": "dock_unknown"}

    # Stop short of the dock for final alignment
    dx = dock["x"] - current_position["x"]
    dy = dock["y"] - current_position["y"]
    total = max(distance(current_position, dock), 0.0001)
    ratio = max(0.0, (total - settings.dock_approach_distance_m) / total)
    approach_point = {
        "x": round(current_position["x"] + dx * ratio, 4),
        "y": round(current_position["y"] + dy * ratio, 4),
    }

    plan = {
        "planned": True,
        "approach_point": approach_point,
        "dock_position": dict(dock),
        "suggested_action": {
            "type": "navigation.plan_to_point",
            "payload": {"goal": approach_point},
        },
    }
    state.mode = "approaching"
    state.last_plan = plan
    remember({"event": "plan_approach", **plan})
    return plan

def align(current_position: dict, dock_position: dict | None = None) -> dict:
    dock = dock_position or state.dock_position
    if not dock:
        return {"aligned": False, "reason": "dock_unknown"}

    d = distance(current_position, dock)
    aligned = d <= settings.alignment_tolerance_m
    result = {
        "aligned": aligned,
        "distance_to_dock_m": round(d, 4),
        "dock_position": dict(dock),
        "alignment_tolerance_m": settings.alignment_tolerance_m,
        "suggested_action": None if aligned else {
            "type": "navigation.plan_to_point",
            "payload": {"goal": dict(dock)},
        },
    }
    state.mode = "aligned" if aligned else "aligning"
    remember({"event": "align", **result})
    return result

def begin_charge(confirmed_docked: bool) -> dict:
    if confirmed_docked:
        state.mode = "charging"
        state.charging = True
        result = {"charging": True, "state": "charging"}
    else:
        result = {"charging": False, "state": state.mode, "reason": "dock_not_confirmed"}
    remember({"event": "begin_charge", **result})
    return result

def get_state() -> dict:
    return {
        "dock_name": state.dock_name,
        "dock_position": state.dock_position,
        "mode": state.mode,
        "charging": state.charging,
        "last_plan": state.last_plan,
        "recent_history": state.history[-10:],
    }

def reset_state() -> dict:
    state.dock_name = "charging_dock"
    state.dock_position = None
    state.mode = "idle"
    state.charging = False
    state.last_plan = None
    state.history.clear()
    return get_state()

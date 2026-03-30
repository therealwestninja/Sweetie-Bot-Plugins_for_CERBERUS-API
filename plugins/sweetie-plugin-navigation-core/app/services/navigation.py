from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC
from math import hypot
import uuid

from app.config import settings

def now_iso() -> str:
    return datetime.now(UTC).isoformat()

@dataclass
class NavigationState:
    position: dict = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    active_route: dict | None = None
    recent_routes: list[dict] = field(default_factory=list)

state = NavigationState()

def distance(a: dict, b: dict) -> float:
    return hypot(b["x"] - a["x"], b["y"] - a["y"])

def interpolate_route(start: dict, goal: dict, step_size: float) -> list[dict]:
    total = distance(start, goal)
    if total == 0:
        return [dict(start)]
    steps = max(1, int(total / step_size))
    points = []
    for i in range(steps + 1):
        t = i / steps
        x = start["x"] + (goal["x"] - start["x"]) * t
        y = start["y"] + (goal["y"] - start["y"]) * t
        points.append({"x": round(x, 4), "y": round(y, 4)})
    return points

def set_position(position: dict) -> dict:
    state.position = {"x": float(position["x"]), "y": float(position["y"])}
    return {"position": state.position}

def _store_route(goal: dict, route_points: list[dict], source: str) -> dict:
    route = {
        "route_id": str(uuid.uuid4()),
        "created_at": now_iso(),
        "source": source,
        "start": dict(state.position),
        "goal": goal,
        "waypoints": route_points,
        "status": "planned",
        "goal_tolerance_m": settings.default_goal_tolerance_m,
    }
    state.active_route = route
    state.recent_routes.append(route)
    state.recent_routes = state.recent_routes[-20:]
    return route

def plan_to_point(goal: dict) -> dict:
    goal = {"x": float(goal["x"]), "y": float(goal["y"])}
    route_points = interpolate_route(state.position, goal, settings.default_step_size_m)
    return _store_route(goal, route_points, "point")

def plan_to_location(name: str, locations: dict) -> dict | None:
    loc = locations.get(name)
    if not loc:
        return None
    goal = {"x": float(loc["x"]), "y": float(loc["y"])}
    route_points = interpolate_route(state.position, goal, settings.default_step_size_m)
    route = _store_route(goal, route_points, f"location:{name}")
    route["location_name"] = name
    return route

def follow_route(route_id: str) -> dict | None:
    if not state.active_route or state.active_route["route_id"] != route_id:
        return None
    state.active_route["status"] = "following"
    state.position = dict(state.active_route["goal"])
    state.active_route["status"] = "completed"
    return state.active_route

def cancel_route() -> dict:
    route_id = state.active_route["route_id"] if state.active_route else None
    if state.active_route:
        state.active_route["status"] = "cancelled"
    state.active_route = None
    return {"cancelled": bool(route_id), "route_id": route_id}

def get_route() -> dict | None:
    return state.active_route

def status() -> dict:
    return {
        "position": state.position,
        "active_route": state.active_route,
        "recent_route_count": len(state.recent_routes),
    }

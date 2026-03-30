from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict

from app.models import ActionRegistration

def now_iso():
    return datetime.now(UTC).isoformat()

@dataclass
class ActionEntry:
    action: ActionRegistration
    created_at: str
    updated_at: str

    def dump(self) -> dict:
        return {
            "action": self.action.model_dump(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

@dataclass
class RegistryState:
    actions: Dict[str, ActionEntry] = field(default_factory=dict)
    dispatch_count: int = 0
    recent_dispatches: list[dict] = field(default_factory=list)

state = RegistryState()

def register_action(model: ActionRegistration) -> dict:
    timestamp = now_iso()
    existing = state.actions.get(model.action_name)
    created_at = existing.created_at if existing else timestamp
    entry = ActionEntry(action=model, created_at=created_at, updated_at=timestamp)
    state.actions[model.action_name] = entry
    return entry.dump()

def unregister_action(action_name: str) -> dict:
    removed = state.actions.pop(action_name, None)
    return {"action_name": action_name, "removed": bool(removed)}

def list_actions() -> list[dict]:
    return [entry.dump() for _, entry in sorted(state.actions.items(), key=lambda kv: kv[0])]

def get_action(action_name: str) -> dict | None:
    entry = state.actions.get(action_name)
    return entry.dump() if entry else None

def set_policy(action_name: str, policy: dict) -> dict | None:
    entry = state.actions.get(action_name)
    if not entry:
        return None
    action_data = entry.action.model_dump()
    action_data["policy"] = policy
    updated = ActionRegistration(**action_data)
    timestamp = now_iso()
    state.actions[action_name] = ActionEntry(action=updated, created_at=entry.created_at, updated_at=timestamp)
    return state.actions[action_name].dump()

def dispatch(action_name: str, payload_override: dict) -> dict | None:
    entry = state.actions.get(action_name)
    if not entry:
        return None
    merged_payload = {**entry.action.default_payload, **payload_override}
    envelope = {
        "dispatch_type": entry.action.handler_type,
        "target_plugin": entry.action.target_plugin,
        "execute_request": {
            "type": entry.action.target_action,
            "payload": merged_payload,
        },
        "policy": entry.action.policy,
        "tags": entry.action.tags,
    }
    state.dispatch_count += 1
    state.recent_dispatches.append({
        "action_name": action_name,
        "target_plugin": entry.action.target_plugin,
        "target_action": entry.action.target_action,
        "dispatched_at": now_iso(),
    })
    state.recent_dispatches = state.recent_dispatches[-20:]
    return {
        "action_name": action_name,
        "description": entry.action.description,
        "dispatch_envelope": envelope,
    }

def status() -> dict:
    by_handler = {}
    for entry in state.actions.values():
        handler = entry.action.handler_type
        by_handler[handler] = by_handler.get(handler, 0) + 1
    return {
        "action_count": len(state.actions),
        "dispatch_count": state.dispatch_count,
        "by_handler_type": by_handler,
        "recent_dispatches": state.recent_dispatches,
    }

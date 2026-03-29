from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CharacterState:
    persona_id: str = "sweetie_bot"
    mood: str = "calm"
    focus_target: Optional[str] = None
    active_routine: Optional[str] = None
    active_emote: str = "calm_neutral"
    accessory_scene: Optional[str] = None
    safe_mode: bool = False
    degraded_mode: bool = False
    last_input: Optional[str] = None
    last_reply: Optional[str] = None
    turn_count: int = 0
    session_event_count: int = 0
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StateUpdate:
    mood: Optional[str] = None
    focus_target: Optional[str] = None
    active_routine: Optional[str] = None
    active_emote: Optional[str] = None
    accessory_scene: Optional[str] = None
    safe_mode: Optional[bool] = None
    degraded_mode: Optional[bool] = None
    last_input: Optional[str] = None
    last_reply: Optional[str] = None

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional


def utc_now():
    return datetime.now(timezone.utc)


@dataclass
class ArbitrationDecision:
    allowed: bool
    routine_id: Optional[str]
    reason: str
    cooldown_until: Optional[str] = None
    replaced_active_routine: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "routine_id": self.routine_id,
            "reason": self.reason,
            "cooldown_until": self.cooldown_until,
            "replaced_active_routine": self.replaced_active_routine,
        }


class RoutineArbitrator:
    def __init__(self) -> None:
        self.cooldowns: Dict[str, datetime] = {}
        self.default_cooldown_seconds = {
            "greet_guest": 10,
            "photo_pose": 15,
            "idle_cute": 5,
            "return_to_neutral": 0,
        }
        self.interruptible_routines = {
            "idle_cute": True,
            "greet_guest": True,
            "photo_pose": True,
            "return_to_neutral": True,
        }

    def is_on_cooldown(self, routine_id: str) -> Optional[datetime]:
        until = self.cooldowns.get(routine_id)
        if until and until > utc_now():
            return until
        return None

    def set_cooldown(self, routine_id: str, seconds: Optional[int] = None) -> Optional[str]:
        duration = self.default_cooldown_seconds.get(routine_id, 5) if seconds is None else seconds
        if duration <= 0:
            self.cooldowns.pop(routine_id, None)
            return None
        until = utc_now() + timedelta(seconds=duration)
        self.cooldowns[routine_id] = until
        return until.isoformat()

    def can_interrupt(self, active_routine: Optional[str], requested_routine: str) -> bool:
        if not active_routine:
            return True
        if active_routine == requested_routine:
            return False
        return self.interruptible_routines.get(active_routine, False)

    def arbitrate(
        self,
        *,
        requested_routine: Optional[str],
        active_routine: Optional[str],
        safe_mode: bool = False,
        degraded_mode: bool = False,
    ) -> Dict[str, Any]:
        if not requested_routine:
            return ArbitrationDecision(
                allowed=False,
                routine_id=None,
                reason="no_requested_routine",
            ).to_dict()

        if degraded_mode and requested_routine != "return_to_neutral":
            return ArbitrationDecision(
                allowed=False,
                routine_id=requested_routine,
                reason="degraded_mode_blocks_non_neutral_routines",
            ).to_dict()

        if safe_mode and requested_routine != "return_to_neutral":
            return ArbitrationDecision(
                allowed=False,
                routine_id=requested_routine,
                reason="safe_mode_blocks_non_neutral_routines",
            ).to_dict()

        cooldown_until = self.is_on_cooldown(requested_routine)
        if cooldown_until:
            return ArbitrationDecision(
                allowed=False,
                routine_id=requested_routine,
                reason="routine_on_cooldown",
                cooldown_until=cooldown_until.isoformat(),
            ).to_dict()

        if not self.can_interrupt(active_routine, requested_routine):
            return ArbitrationDecision(
                allowed=False,
                routine_id=requested_routine,
                reason="active_routine_not_interruptible",
            ).to_dict()

        new_cooldown = self.set_cooldown(requested_routine)
        return ArbitrationDecision(
            allowed=True,
            routine_id=requested_routine,
            reason="allowed",
            cooldown_until=new_cooldown,
            replaced_active_routine=active_routine if active_routine and active_routine != requested_routine else None,
        ).to_dict()

    def snapshot(self) -> Dict[str, Any]:
        now = utc_now()
        active = {
            routine_id: until.isoformat()
            for routine_id, until in self.cooldowns.items()
            if until > now
        }
        return {
            "default_cooldown_seconds": dict(self.default_cooldown_seconds),
            "interruptible_routines": dict(self.interruptible_routines),
            "active_cooldowns": active,
        }

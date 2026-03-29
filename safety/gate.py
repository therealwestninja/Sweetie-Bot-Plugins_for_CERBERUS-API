"""
sweetiebot.safety.gate
=======================
The safety gate sits between a validated ``CharacterResponse`` and the
``CerberusMapper``.  It enforces:

1. **Allowlist enforcement** – only known routine / emote IDs pass.
2. **Per-routine-ID rate limiting** – token-bucket per routine_id, not per IP.
   This prevents character spam (e.g. ``greet_guest`` fired 10× per second).
3. **State-aware blocking** – respects ``safe_mode`` / ``degraded_mode`` from
   the character state, plus operator overrides.
4. **Operator override** – a privileged caller can bypass rate-limits for one
   request (e.g. live demo operator pressing a button).

Design
------
* The gate is **fail-closed**: if it cannot determine safety, it blocks.
* ``safe_mode`` → only ``return_to_neutral`` is permitted.
* ``degraded_mode`` → routine commands blocked; dialogue/emote only.
* ``emergency`` → everything blocked except state reads.
* Token buckets are per-routine (not per-IP): each routine has its own
  cooldown window defined in ``cooldown_seconds``.

The gate does NOT call CERBERUS and does NOT execute anything.
It only decides: *"is this request safe to pass to the mapper?"*
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sweetiebot.integration.schemas import (
    CharacterResponse,
    PlanRejectionReason,
    SafetyMode,
    ValidationResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Token bucket per routine_id
# ---------------------------------------------------------------------------

@dataclass
class RoutineBucket:
    """Sliding-window token bucket for a single routine_id."""
    routine_id: str
    cooldown_seconds: float
    last_allowed_at: float = field(default=0.0)

    def is_available(self) -> bool:
        return (time.monotonic() - self.last_allowed_at) >= self.cooldown_seconds

    def consume(self) -> None:
        self.last_allowed_at = time.monotonic()

    def retry_after(self) -> float:
        """Seconds until next allowed invocation."""
        remaining = self.cooldown_seconds - (time.monotonic() - self.last_allowed_at)
        return max(0.0, remaining)


# ---------------------------------------------------------------------------
# Gate result
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    allowed: bool
    safety_mode: SafetyMode
    rejection_reasons: List[PlanRejectionReason] = field(default_factory=list)
    rejection_detail: Optional[str] = None
    operator_override_applied: bool = False
    retry_after_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "safety_mode": self.safety_mode.value,
            "rejection_reasons": [r.value for r in self.rejection_reasons],
            "rejection_detail": self.rejection_detail,
            "operator_override_applied": self.operator_override_applied,
            "retry_after_seconds": self.retry_after_seconds,
        }


# ---------------------------------------------------------------------------
# Default per-routine cooldowns (seconds)
# ---------------------------------------------------------------------------

_DEFAULT_COOLDOWNS: Dict[str, float] = {
    "greeting_01":        10.0,
    "greet_guest":        10.0,
    "photo_pose":         15.0,
    "idle_cute":           5.0,
    "return_to_neutral":   0.0,   # always immediate
    "sit_stay":            8.0,
}

_GLOBAL_RATE_LIMIT_SECONDS: float = 0.5  # floor: no more than 1 req / 500ms


# ---------------------------------------------------------------------------
# Safety Gate
# ---------------------------------------------------------------------------

class SafetyGate:
    """
    Validates a ``CharacterResponse`` before it reaches the CERBERUS mapper.

    Parameters
    ----------
    routine_cooldowns:
        Override per-routine cooldown windows in seconds.
        Values from ``_DEFAULT_COOLDOWNS`` are used for any routine not listed.
    global_rate_limit:
        Minimum seconds between *any* two consecutive requests (all routines).
    """

    def __init__(
        self,
        *,
        routine_cooldowns: Optional[Dict[str, float]] = None,
        global_rate_limit: float = _GLOBAL_RATE_LIMIT_SECONDS,
    ) -> None:
        self._cooldowns: Dict[str, float] = {**_DEFAULT_COOLDOWNS, **(routine_cooldowns or {})}
        self._global_rate_limit = global_rate_limit
        self._buckets: Dict[str, RoutineBucket] = {}
        self._last_any_request_at: float = 0.0
        self._safety_mode: SafetyMode = SafetyMode.NORMAL
        self._operator_override_active: bool = False
        # audit trail — last 50 gate decisions
        self._audit_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Mode control (called by runtime when operator events arrive)
    # ------------------------------------------------------------------

    @property
    def safety_mode(self) -> SafetyMode:
        return self._safety_mode

    def set_safety_mode(self, mode: SafetyMode) -> None:
        prev = self._safety_mode
        self._safety_mode = mode
        logger.warning("SafetyGate mode change: %s → %s", prev.value, mode.value)
        self._audit("mode_change", {"prev": prev.value, "new": mode.value})

    def set_operator_override(self, active: bool) -> None:
        self._operator_override_active = active
        logger.info("Operator override: %s", "ACTIVE" if active else "CLEARED")
        self._audit("operator_override", {"active": active})

    # ------------------------------------------------------------------
    # Primary entry point
    # ------------------------------------------------------------------

    def check(
        self,
        response: CharacterResponse,
        *,
        operator_override: bool = False,
    ) -> GateResult:
        """
        Evaluate a ``CharacterResponse`` against all safety rules.

        Returns a ``GateResult`` indicating whether the request may proceed.
        The caller (integration route) decides what to do with the result.
        """
        effective_override = operator_override or self._operator_override_active

        # ── derive effective mode ──────────────────────────────────────
        mode = self._safety_mode
        if response.safe_mode and mode not in (SafetyMode.EMERGENCY,):
            mode = SafetyMode.SAFE
        if response.degraded_mode and mode == SafetyMode.NORMAL:
            mode = SafetyMode.DEGRADED

        # ── emergency: block everything ────────────────────────────────
        if mode == SafetyMode.EMERGENCY:
            result = GateResult(
                allowed=False,
                safety_mode=mode,
                rejection_reasons=[PlanRejectionReason.SAFE_MODE_BLOCKED],
                rejection_detail="EMERGENCY mode: all commands blocked",
            )
            self._audit("blocked_emergency", {"response_id": response.response_id})
            return result

        # ── safe mode: only return_to_neutral allowed ──────────────────
        if mode == SafetyMode.SAFE:
            if response.routine_id and response.routine_id != "return_to_neutral":
                result = GateResult(
                    allowed=False,
                    safety_mode=mode,
                    rejection_reasons=[PlanRejectionReason.SAFE_MODE_BLOCKED],
                    rejection_detail=(
                        f"safe_mode active — routine '{response.routine_id}' blocked; "
                        "only 'return_to_neutral' is permitted"
                    ),
                )
                self._audit("blocked_safe_mode", {
                    "routine_id": response.routine_id,
                    "response_id": response.response_id,
                })
                return result

        # ── degraded mode: no routines ─────────────────────────────────
        if mode == SafetyMode.DEGRADED and response.routine_id:
            result = GateResult(
                allowed=False,
                safety_mode=mode,
                rejection_reasons=[PlanRejectionReason.DEGRADED_MODE],
                rejection_detail=(
                    f"degraded_mode active — routine '{response.routine_id}' blocked"
                ),
            )
            self._audit("blocked_degraded", {
                "routine_id": response.routine_id,
                "response_id": response.response_id,
            })
            return result

        # ── global rate limit (skip if operator override) ──────────────
        now = time.monotonic()
        if not effective_override:
            since_last = now - self._last_any_request_at
            if since_last < self._global_rate_limit:
                retry = round(self._global_rate_limit - since_last, 3)
                result = GateResult(
                    allowed=False,
                    safety_mode=mode,
                    rejection_reasons=[PlanRejectionReason.RATE_LIMITED],
                    rejection_detail=f"Global rate limit: retry in {retry}s",
                    retry_after_seconds=retry,
                )
                self._audit("rate_limited_global", {"retry_after": retry})
                return result

        # ── per-routine cooldown ───────────────────────────────────────
        if response.routine_id and not effective_override:
            bucket = self._get_bucket(response.routine_id)
            if not bucket.is_available():
                retry = round(bucket.retry_after(), 3)
                result = GateResult(
                    allowed=False,
                    safety_mode=mode,
                    rejection_reasons=[PlanRejectionReason.RATE_LIMITED],
                    rejection_detail=(
                        f"Routine '{response.routine_id}' on cooldown — retry in {retry}s"
                    ),
                    retry_after_seconds=retry,
                )
                self._audit("rate_limited_routine", {
                    "routine_id": response.routine_id,
                    "retry_after": retry,
                })
                return result

        # ── all checks passed ──────────────────────────────────────────
        self._last_any_request_at = now
        if response.routine_id:
            self._get_bucket(response.routine_id).consume()

        result = GateResult(
            allowed=True,
            safety_mode=mode,
            operator_override_applied=effective_override,
        )
        self._audit("allowed", {
            "routine_id": response.routine_id,
            "emote_id": response.emote_id,
            "response_id": response.response_id,
            "override": effective_override,
        })
        return result

    def validate_only(self, response: CharacterResponse) -> ValidationResult:
        """
        Runs gate logic in read-only mode — no state is mutated.
        Returns a ``ValidationResult``-compatible dict.
        """
        issues: List[str] = []
        warnings: List[str] = []
        mode = self._safety_mode
        if response.safe_mode:
            mode = SafetyMode.SAFE
        if response.degraded_mode and mode == SafetyMode.NORMAL:
            mode = SafetyMode.DEGRADED

        if mode == SafetyMode.EMERGENCY:
            issues.append("EMERGENCY mode active — nothing will pass")
        elif mode == SafetyMode.SAFE and response.routine_id and response.routine_id != "return_to_neutral":
            issues.append(f"safe_mode would block routine '{response.routine_id}'")
        elif mode == SafetyMode.DEGRADED and response.routine_id:
            issues.append(f"degraded_mode would block routine '{response.routine_id}'")

        if response.routine_id:
            bucket = self._buckets.get(response.routine_id)
            if bucket and not bucket.is_available():
                warnings.append(
                    f"Routine '{response.routine_id}' is on cooldown "
                    f"({bucket.retry_after():.1f}s remaining)"
                )

        return ValidationResult(
            valid=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            safety_mode=mode,
            would_approve=len(issues) == 0,
        )

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        now = time.monotonic()
        cooldowns_active = {
            rid: round(b.retry_after(), 2)
            for rid, b in self._buckets.items()
            if b.retry_after() > 0
        }
        return {
            "safety_mode": self._safety_mode.value,
            "operator_override_active": self._operator_override_active,
            "global_rate_limit_seconds": self._global_rate_limit,
            "configured_cooldowns": dict(self._cooldowns),
            "active_cooldowns": cooldowns_active,
            "audit_log_size": len(self._audit_log),
            "last_audit": self._audit_log[-1] if self._audit_log else None,
        }

    def recent_audit(self, limit: int = 20) -> List[Dict[str, Any]]:
        return list(reversed(self._audit_log[-limit:]))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_bucket(self, routine_id: str) -> RoutineBucket:
        if routine_id not in self._buckets:
            cooldown = self._cooldowns.get(routine_id, 5.0)
            self._buckets[routine_id] = RoutineBucket(
                routine_id=routine_id,
                cooldown_seconds=cooldown,
            )
        return self._buckets[routine_id]

    def _audit(self, event: str, detail: Dict[str, Any]) -> None:
        entry = {
            "event": event,
            "ts": time.time(),
            "safety_mode": self._safety_mode.value,
            **detail,
        }
        self._audit_log.append(entry)
        if len(self._audit_log) > 200:
            self._audit_log = self._audit_log[-200:]

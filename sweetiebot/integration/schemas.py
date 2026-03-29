"""
sweetiebot.integration.schemas
==============================
Formal, versioned Pydantic v2 models for the Sweetie-Bot ↔ CERBERUS integration contract.

These are the *only* types that cross the boundary between Sweetie-Bot (character layer)
and CERBERUS (robot control layer).  Nothing else is accepted at the API boundary.

Design rules
------------
* All fields have explicit types — no plain ``dict`` fields in the contract.
* Every top-level model carries ``schema_version`` for forward-compat.
* All timestamps are ISO-8601 UTC strings (``datetime`` would require timezone
  handling at the JSON boundary, which is error-prone).
* Enums are ``str`` sub-classes so they serialise cleanly to JSON.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid4())


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class MoodLabel(StrEnum):
    CALM       = "calm"
    CURIOUS    = "curious"
    HAPPY      = "happy"
    EXCITED    = "excited"
    BASHFUL    = "bashful"
    APOLOGETIC = "apologetic"
    PROTECTIVE = "protective"
    SLEEPY     = "sleepy"
    UNKNOWN    = "unknown"


class SafetyMode(StrEnum):
    NORMAL    = "normal"
    SAFE      = "safe"
    DEGRADED  = "degraded"
    EMERGENCY = "emergency"


class CommandType(StrEnum):
    ROUTINE   = "routine"
    EMOTE     = "emote"
    ACCESSORY = "accessory"
    AUDIO     = "audio"
    STATE     = "state"


class OperatorEventKind(StrEnum):
    STOP          = "stop"
    RESET         = "reset"
    SAFE_MODE     = "safe_mode"
    OVERRIDE      = "override"
    MOOD_INJECT   = "mood_inject"
    ROUTINE_FORCE = "routine_force"


class PlanRejectionReason(StrEnum):
    UNKNOWN_ROUTINE      = "unknown_routine"
    UNKNOWN_EMOTE        = "unknown_emote"
    UNKNOWN_ACCESSORY    = "unknown_accessory"
    RATE_LIMITED         = "rate_limited"
    SAFE_MODE_BLOCKED    = "safe_mode_blocked"
    DEGRADED_MODE        = "degraded_mode"
    ALLOWLIST_VIOLATION  = "allowlist_violation"
    VALIDATION_ERROR     = "validation_error"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class RoutineMapping(BaseModel):
    """A single routine that Sweetie-Bot may request."""
    routine_id: str
    cerberus_command: str
    description: str = ""
    estimated_duration_ms: int = Field(default=3000, ge=0)
    requires_safe_mode: bool = False
    tags: List[str] = Field(default_factory=list)


class EmoteMapping(BaseModel):
    """A single emote → CERBERUS animation mapping."""
    emote_id: str
    cerberus_animation: str
    accessory_scene_id: Optional[str] = None
    duration_ms: int = Field(default=1500, ge=0)
    tags: List[str] = Field(default_factory=list)


class AccessoryMapping(BaseModel):
    """An accessory scene → CERBERUS accessory state mapping."""
    scene_id: str
    cerberus_state: str
    description: str = ""
    tags: List[str] = Field(default_factory=list)


class AudioCueSpec(BaseModel):
    """An audio cue to be played by CERBERUS."""
    cue_id: str
    file_hint: Optional[str] = None   # logical name; CERBERUS resolves actual file
    volume: float = Field(default=0.8, ge=0.0, le=1.0)
    loop: bool = False


# ---------------------------------------------------------------------------
# Core contract models
# ---------------------------------------------------------------------------

class CharacterResponse(BaseModel):
    """
    The structured output produced by Sweetie-Bot after processing any input.
    This is the *only* type that CERBERUS should accept from Sweetie-Bot.
    """
    schema_version: Literal["1.0"] = "1.0"
    response_id: str = Field(default_factory=_new_id)
    timestamp: str = Field(default_factory=_utc_now)

    # ── text / speech ──────────────────────────────────────────────────────
    reply_text: Optional[str] = Field(
        default=None,
        description="The text Sweetie-Bot would speak or display.",
    )

    # ── physical intent ────────────────────────────────────────────────────
    emote_id: Optional[str] = Field(
        default=None,
        description="Emote identifier (must be in the allowlist).",
    )
    routine_id: Optional[str] = Field(
        default=None,
        description="Routine identifier (must be in the allowlist).",
    )
    accessory_scene_id: Optional[str] = Field(
        default=None,
        description="Accessory scene identifier (must be in the allowlist).",
    )
    audio_cue: Optional[AudioCueSpec] = None

    # ── mode flags ─────────────────────────────────────────────────────────
    safe_mode: bool = Field(
        default=False,
        description="If True, CERBERUS must transition to safe-mode posture.",
    )
    degraded_mode: bool = Field(
        default=False,
        description="If True, only minimal actions are permitted.",
    )

    # ── metadata ───────────────────────────────────────────────────────────
    mood: MoodLabel = MoodLabel.CALM
    intent: Optional[str] = None
    source: str = "sweetiebot"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("reply_text")
    @classmethod
    def _check_reply_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 2000:
            raise ValueError("reply_text exceeds maximum length of 2000 characters")
        return v

    @model_validator(mode="after")
    def _check_safe_degraded_consistency(self) -> "CharacterResponse":
        if self.safe_mode and self.routine_id and self.routine_id != "return_to_neutral":
            raise ValueError(
                "safe_mode=True requires routine_id to be None or 'return_to_neutral'"
            )
        return self


class CharacterState(BaseModel):
    """
    A point-in-time snapshot of Sweetie-Bot's internal state,
    suitable for transmission to CERBERUS or the Web UI.
    """
    schema_version: Literal["1.0"] = "1.0"
    snapshot_id: str = Field(default_factory=_new_id)
    timestamp: str = Field(default_factory=_utc_now)

    persona_id: str = "sweetie_bot"
    mood: MoodLabel = MoodLabel.CALM
    safety_mode: SafetyMode = SafetyMode.NORMAL
    focus_target: Optional[str] = None
    active_routine: Optional[str] = None
    active_emote: Optional[str] = None
    active_accessory_scene: Optional[str] = None
    turn_count: int = 0
    session_event_count: int = 0
    last_input: Optional[str] = None
    last_reply: Optional[str] = None


class OperatorEvent(BaseModel):
    """
    An event sent by the human operator (via the Web UI or direct API).
    Operators can override character decisions or inject safety signals.
    """
    schema_version: Literal["1.0"] = "1.0"
    event_id: str = Field(default_factory=_new_id)
    timestamp: str = Field(default_factory=_utc_now)

    kind: OperatorEventKind
    payload: Dict[str, Any] = Field(default_factory=dict)
    operator_id: str = "operator"
    override: bool = False
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# CERBERUS execution models
# ---------------------------------------------------------------------------

class CerberusCommand(BaseModel):
    """A single executable command for CERBERUS."""
    command_type: CommandType
    command_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class IntegrationPlan(BaseModel):
    """
    The output of the CERBERUS mapper: an ordered list of commands to execute.
    CERBERUS decides whether to actually run them — Sweetie-Bot only *proposes*.
    """
    schema_version: Literal["1.0"] = "1.0"
    plan_id: str = Field(default_factory=_new_id)
    timestamp: str = Field(default_factory=_utc_now)

    source_response_id: str
    approved: bool
    commands: List[CerberusCommand] = Field(default_factory=list)
    dry_run: bool = False
    rejection_reasons: List[PlanRejectionReason] = Field(default_factory=list)
    rejection_detail: Optional[str] = None
    safety_mode_at_planning: SafetyMode = SafetyMode.NORMAL


class ValidationResult(BaseModel):
    """Result of running safety + mapping validation against a CharacterResponse."""
    schema_version: Literal["1.0"] = "1.0"
    timestamp: str = Field(default_factory=_utc_now)

    valid: bool
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    safety_mode: SafetyMode = SafetyMode.NORMAL
    would_approve: bool = False


class CapabilityManifest(BaseModel):
    """
    What Sweetie-Bot may request — the intersection of what is configured
    and what CERBERUS currently supports.
    """
    schema_version: Literal["1.0"] = "1.0"
    timestamp: str = Field(default_factory=_utc_now)

    routines: List[RoutineMapping] = Field(default_factory=list)
    emotes: List[EmoteMapping] = Field(default_factory=list)
    accessories: List[AccessoryMapping] = Field(default_factory=list)
    safety_mode: SafetyMode = SafetyMode.NORMAL
    dry_run_mode: bool = False


# ---------------------------------------------------------------------------
# WebSocket event envelope
# ---------------------------------------------------------------------------

class WSEventType(StrEnum):
    INTEGRATION_PLAN_CREATED   = "integration.plan.created"
    INTEGRATION_PLAN_REJECTED  = "integration.plan.rejected"
    CHARACTER_STATE_UPDATED    = "character.state.updated"
    SAFETY_MODE_CHANGED        = "safety.mode.changed"
    EVENTS_SNAPSHOT            = "events.snapshot"
    PERSONA_SELECTED           = "persona.selected"
    DIALOGUE_GENERATED         = "dialogue.generated"
    EMOTE_MAPPED               = "emote.mapped"
    ROUTINE_ARBITRATED         = "routine.arbitrated"
    OPERATOR_EVENT             = "operator.event"


class WSEvent(BaseModel):
    """Consistent envelope for all WebSocket events."""
    schema_version: Literal["1.0"] = "1.0"
    event_id: str = Field(default_factory=_new_id)
    timestamp: str = Field(default_factory=_utc_now)
    event_type: WSEventType
    payload: Dict[str, Any] = Field(default_factory=dict)
    # replay_safe: True means the event carries enough context to reconstruct
    # the relevant state from nothing (useful for UI reconnections).
    replay_safe: bool = False

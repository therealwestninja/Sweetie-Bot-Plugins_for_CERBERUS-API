"""
sweetiebot.integration.cerberus_mapper
========================================
Translates a validated ``CharacterResponse`` into an ordered list of
``CerberusCommand`` objects that CERBERUS can execute.

Design contract
---------------
* NEVER emits a command that is not in its allowlists.
* Unknown IDs → plan is rejected, reason is recorded.
* dry_run=True → plan is built and validated but commands are flagged
  as non-executable (safe for testing the pipeline end-to-end).
* The mapper is stateless; safety-mode awareness lives in ``safety.gate``.
* All mapping tables are loaded at construction time and can be reloaded
  via ``reload_mappings()``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sweetiebot.integration.schemas import (
    AccessoryMapping,
    AudioCueSpec,
    CapabilityManifest,
    CerberusCommand,
    CharacterResponse,
    CommandType,
    EmoteMapping,
    IntegrationPlan,
    PlanRejectionReason,
    RoutineMapping,
    SafetyMode,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Built-in mapping tables
# These represent the *default* Sweetie-Bot ↔ CERBERUS vocabulary.
# Operators can extend these at runtime via reload_mappings().
# ---------------------------------------------------------------------------

_DEFAULT_ROUTINES: List[Dict[str, Any]] = [
    {
        "routine_id": "greeting_01",
        "cerberus_command": "sport.greeting_sequence_01",
        "description": "Standard guest greeting with tail wag and head bow",
        "estimated_duration_ms": 3200,
        "tags": ["social", "greeting"],
    },
    {
        "routine_id": "greet_guest",
        "cerberus_command": "sport.greet_guest",
        "description": "Approaches guest position, head-nod, step back",
        "estimated_duration_ms": 4000,
        "tags": ["social", "greeting"],
    },
    {
        "routine_id": "photo_pose",
        "cerberus_command": "sport.photo_pose_hold",
        "description": "Holds a photogenic pose, minimal movement",
        "estimated_duration_ms": 8000,
        "tags": ["performance", "pose"],
    },
    {
        "routine_id": "idle_cute",
        "cerberus_command": "sport.idle_cute_loop",
        "description": "Gentle idle animation — head sways, weight shifts",
        "estimated_duration_ms": 6000,
        "tags": ["idle"],
    },
    {
        "routine_id": "return_to_neutral",
        "cerberus_command": "sport.return_to_stand_neutral",
        "description": "Returns to standing neutral posture; always allowed",
        "estimated_duration_ms": 2000,
        "tags": ["safety", "neutral"],
        "requires_safe_mode": False,
    },
    {
        "routine_id": "sit_stay",
        "cerberus_command": "sport.sit_and_stay",
        "description": "Sits and holds still",
        "estimated_duration_ms": 5000,
        "tags": ["calm", "pose"],
    },
]

_DEFAULT_EMOTES: List[Dict[str, Any]] = [
    {
        "emote_id": "curious_headtilt",
        "cerberus_animation": "anim.head_tilt_curious",
        "accessory_scene_id": "eyes_curious",
        "duration_ms": 1500,
        "tags": ["curious"],
    },
    {
        "emote_id": "warm_smile",
        "cerberus_animation": "anim.face_warm_smile",
        "accessory_scene_id": "eyes_happy",
        "duration_ms": 2000,
        "tags": ["happy", "friendly"],
    },
    {
        "emote_id": "calm_neutral",
        "cerberus_animation": "anim.face_neutral_calm",
        "accessory_scene_id": None,
        "duration_ms": 1000,
        "tags": ["neutral", "calm"],
    },
    {
        "emote_id": "happy_bounce",
        "cerberus_animation": "anim.body_happy_bounce",
        "accessory_scene_id": "eyes_happy",
        "duration_ms": 2500,
        "tags": ["happy", "excited"],
    },
    {
        "emote_id": "happy_pose",
        "cerberus_animation": "anim.face_happy_pose",
        "accessory_scene_id": "eyes_happy",
        "duration_ms": 2000,
        "tags": ["happy"],
    },
    {
        "emote_id": "sleepy_blink",
        "cerberus_animation": "anim.face_sleepy_blink",
        "accessory_scene_id": None,
        "duration_ms": 1800,
        "tags": ["sleepy"],
    },
    {
        "emote_id": "bashful_shift",
        "cerberus_animation": "anim.body_bashful_weight_shift",
        "accessory_scene_id": None,
        "duration_ms": 1500,
        "tags": ["bashful"],
    },
    {
        "emote_id": "curious_tilt",
        "cerberus_animation": "anim.head_tilt_curious_alt",
        "accessory_scene_id": "eyes_curious",
        "duration_ms": 1200,
        "tags": ["curious"],
    },
]

_DEFAULT_ACCESSORIES: List[Dict[str, Any]] = [
    {
        "scene_id": "eyes_happy",
        "cerberus_state": "accessory.eyes.scene_happy",
        "description": "Happy, bright eye expression",
        "tags": ["eyes", "happy"],
    },
    {
        "scene_id": "eyes_curious",
        "cerberus_state": "accessory.eyes.scene_curious",
        "description": "Wide, curious eye expression",
        "tags": ["eyes", "curious"],
    },
    {
        "scene_id": "eyes_neutral",
        "cerberus_state": "accessory.eyes.scene_neutral",
        "description": "Neutral resting eye expression",
        "tags": ["eyes", "neutral"],
    },
    {
        "scene_id": "eyes_sleepy",
        "cerberus_state": "accessory.eyes.scene_sleepy",
        "description": "Half-closed sleepy eye expression",
        "tags": ["eyes", "sleepy"],
    },
]


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------

class CerberusMapper:
    """
    Translates a ``CharacterResponse`` into an ``IntegrationPlan``.

    Parameters
    ----------
    dry_run:
        If True, all generated plans are marked non-executable. Commands are
        still built and validated so the pipeline can be tested safely.
    extra_routines / extra_emotes / extra_accessories:
        Additional mapping entries to merge with the built-in defaults.
    """

    def __init__(
        self,
        *,
        dry_run: bool = False,
        extra_routines: Optional[List[Dict[str, Any]]] = None,
        extra_emotes: Optional[List[Dict[str, Any]]] = None,
        extra_accessories: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.dry_run = dry_run
        self._routines: Dict[str, RoutineMapping] = {}
        self._emotes: Dict[str, EmoteMapping] = {}
        self._accessories: Dict[str, AccessoryMapping] = {}
        self.reload_mappings(
            routines=_DEFAULT_ROUTINES + (extra_routines or []),
            emotes=_DEFAULT_EMOTES + (extra_emotes or []),
            accessories=_DEFAULT_ACCESSORIES + (extra_accessories or []),
        )
        logger.info(
            "CerberusMapper initialised — routines=%d emotes=%d accessories=%d dry_run=%s",
            len(self._routines),
            len(self._emotes),
            len(self._accessories),
            dry_run,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reload_mappings(
        self,
        *,
        routines: Optional[List[Dict[str, Any]]] = None,
        emotes: Optional[List[Dict[str, Any]]] = None,
        accessories: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Hot-reload mapping tables without restarting the runtime."""
        if routines is not None:
            self._routines = {
                r["routine_id"]: RoutineMapping(**r) for r in routines
            }
        if emotes is not None:
            self._emotes = {
                e["emote_id"]: EmoteMapping(**e) for e in emotes
            }
        if accessories is not None:
            self._accessories = {
                a["scene_id"]: AccessoryMapping(**a) for a in accessories
            }

    def plan(
        self,
        response: CharacterResponse,
        *,
        safety_mode: SafetyMode = SafetyMode.NORMAL,
        dry_run: Optional[bool] = None,
    ) -> IntegrationPlan:
        """
        Build an ``IntegrationPlan`` from a ``CharacterResponse``.

        The plan is *approved* only when every requested action maps to an
        allowlisted entry. A single unknown ID rejects the entire plan.
        """
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        commands: List[CerberusCommand] = []
        rejections: List[PlanRejectionReason] = []
        rejection_detail_parts: List[str] = []

        # ── emote ──────────────────────────────────────────────────────
        if response.emote_id:
            result = self._map_emote(response.emote_id, commands)
            if result:
                rejections.append(result[0])
                rejection_detail_parts.append(result[1])

        # ── routine ────────────────────────────────────────────────────
        if response.routine_id:
            result = self._map_routine(response.routine_id, commands, safety_mode)
            if result:
                rejections.append(result[0])
                rejection_detail_parts.append(result[1])

        # ── accessory scene ────────────────────────────────────────────
        if response.accessory_scene_id:
            result = self._map_accessory(response.accessory_scene_id, commands)
            if result:
                rejections.append(result[0])
                rejection_detail_parts.append(result[1])

        # ── audio cue ──────────────────────────────────────────────────
        if response.audio_cue:
            self._map_audio(response.audio_cue, commands)

        approved = len(rejections) == 0

        plan = IntegrationPlan(
            source_response_id=response.response_id,
            approved=approved and not effective_dry_run,
            commands=commands if approved else [],
            dry_run=effective_dry_run,
            rejection_reasons=rejections,
            rejection_detail="; ".join(rejection_detail_parts) or None,
            safety_mode_at_planning=safety_mode,
        )

        level = "info" if approved else "warning"
        logger.log(
            logging.getLevelName(level.upper()),
            "Integration plan %s | approved=%s dry_run=%s commands=%d rejections=%s",
            plan.plan_id,
            approved,
            effective_dry_run,
            len(plan.commands),
            [r.value for r in rejections],
        )
        return plan

    def validate(self, response: CharacterResponse) -> Dict[str, Any]:
        """
        Dry-run validation only — does not build a real plan.
        Returns a dict compatible with ``ValidationResult``.
        """
        issues: List[str] = []
        warnings: List[str] = []

        if response.emote_id and response.emote_id not in self._emotes:
            issues.append(f"Unknown emote_id: '{response.emote_id}'")

        if response.routine_id and response.routine_id not in self._routines:
            issues.append(f"Unknown routine_id: '{response.routine_id}'")

        if response.accessory_scene_id and response.accessory_scene_id not in self._accessories:
            issues.append(f"Unknown accessory_scene_id: '{response.accessory_scene_id}'")

        if response.safe_mode and response.routine_id and response.routine_id != "return_to_neutral":
            warnings.append(
                "safe_mode=True with a non-neutral routine — routine will be blocked by safety gate"
            )

        if response.reply_text and len(response.reply_text) > 500:
            warnings.append("reply_text is very long (>500 chars); may truncate in UI")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "would_approve": len(issues) == 0,
        }

    def capabilities(self, safety_mode: SafetyMode = SafetyMode.NORMAL) -> CapabilityManifest:
        """Return the current capability manifest visible to CERBERUS."""
        routines = list(self._routines.values())
        if safety_mode in (SafetyMode.SAFE, SafetyMode.DEGRADED, SafetyMode.EMERGENCY):
            routines = [r for r in routines if not r.requires_safe_mode or r.routine_id == "return_to_neutral"]

        return CapabilityManifest(
            routines=routines,
            emotes=list(self._emotes.values()),
            accessories=list(self._accessories.values()),
            safety_mode=safety_mode,
            dry_run_mode=self.dry_run,
        )

    def snapshot(self) -> Dict[str, Any]:
        return {
            "routine_count": len(self._routines),
            "emote_count": len(self._emotes),
            "accessory_count": len(self._accessories),
            "dry_run": self.dry_run,
            "routine_ids": sorted(self._routines.keys()),
            "emote_ids": sorted(self._emotes.keys()),
            "accessory_ids": sorted(self._accessories.keys()),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _map_routine(
        self,
        routine_id: str,
        commands: List[CerberusCommand],
        safety_mode: SafetyMode,
    ) -> Optional[tuple[PlanRejectionReason, str]]:
        mapping = self._routines.get(routine_id)
        if mapping is None:
            return (
                PlanRejectionReason.UNKNOWN_ROUTINE,
                f"routine_id '{routine_id}' not in allowlist",
            )
        if safety_mode in (SafetyMode.SAFE, SafetyMode.DEGRADED, SafetyMode.EMERGENCY):
            if routine_id != "return_to_neutral":
                return (
                    PlanRejectionReason.SAFE_MODE_BLOCKED,
                    f"routine_id '{routine_id}' blocked in safety_mode={safety_mode}",
                )
        commands.append(CerberusCommand(
            command_type=CommandType.ROUTINE,
            command_id=mapping.cerberus_command,
            parameters={
                "routine_id": routine_id,
                "estimated_duration_ms": mapping.estimated_duration_ms,
                "tags": mapping.tags,
            },
        ))
        return None

    def _map_emote(
        self,
        emote_id: str,
        commands: List[CerberusCommand],
    ) -> Optional[tuple[PlanRejectionReason, str]]:
        mapping = self._emotes.get(emote_id)
        if mapping is None:
            return (
                PlanRejectionReason.UNKNOWN_EMOTE,
                f"emote_id '{emote_id}' not in allowlist",
            )
        commands.append(CerberusCommand(
            command_type=CommandType.EMOTE,
            command_id=mapping.cerberus_animation,
            parameters={
                "emote_id": emote_id,
                "duration_ms": mapping.duration_ms,
                "tags": mapping.tags,
            },
        ))
        # If this emote implies an accessory scene, include it automatically
        if mapping.accessory_scene_id:
            acc = self._accessories.get(mapping.accessory_scene_id)
            if acc:
                commands.append(CerberusCommand(
                    command_type=CommandType.ACCESSORY,
                    command_id=acc.cerberus_state,
                    parameters={"scene_id": mapping.accessory_scene_id, "source": "emote_implied"},
                ))
        return None

    def _map_accessory(
        self,
        scene_id: str,
        commands: List[CerberusCommand],
    ) -> Optional[tuple[PlanRejectionReason, str]]:
        mapping = self._accessories.get(scene_id)
        if mapping is None:
            return (
                PlanRejectionReason.UNKNOWN_ACCESSORY,
                f"accessory_scene_id '{scene_id}' not in allowlist",
            )
        # Avoid duplicate if emote already added this scene
        already = any(
            c.command_type == CommandType.ACCESSORY and
            c.parameters.get("scene_id") == scene_id
            for c in commands
        )
        if not already:
            commands.append(CerberusCommand(
                command_type=CommandType.ACCESSORY,
                command_id=mapping.cerberus_state,
                parameters={"scene_id": scene_id},
            ))
        return None

    def _map_audio(
        self,
        audio_cue: AudioCueSpec,
        commands: List[CerberusCommand],
    ) -> None:
        # Audio cues are pass-through — CERBERUS resolves the actual file.
        # We don't allowlist audio cue IDs (they're controlled by CERBERUS assets).
        commands.append(CerberusCommand(
            command_type=CommandType.AUDIO,
            command_id=f"audio.play.{audio_cue.cue_id}",
            parameters={
                "cue_id": audio_cue.cue_id,
                "file_hint": audio_cue.file_hint,
                "volume": audio_cue.volume,
                "loop": audio_cue.loop,
            },
        ))

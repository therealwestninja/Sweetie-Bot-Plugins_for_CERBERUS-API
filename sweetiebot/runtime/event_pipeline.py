"""
sweetiebot.runtime.event_pipeline
===================================
Normalised event ingestion layer for Sweetie-Bot.

Events arrive from multiple sources (operator, sensors, hardware)
and must be normalised into a common schema before they influence
character state or trigger actions.

Event sources
-------------
* Operator (web UI, API)
* Speech transcription (STT — future)
* Vision / proximity sensors
* Hardware watchdogs (battery, faults)

Pipeline stages
---------------
1. Ingest raw event (any source)
2. Normalise to SweetieBotEvent schema
3. Update character state
4. Emit to the event hub (WebSocket subscribers)
5. Return recommended action hints (never commands)

Design rules
------------
* Events NEVER directly execute robot actions
* All state changes go through CharacterStateManager
* Safety-critical events (fault, proximity_alert) set safe/degraded mode
  via the SafetyGate — they do not bypass it
* The pipeline is synchronous; async wrappers live in the API layer
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Dict, List, Optional
from uuid import uuid4

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event schema
# ---------------------------------------------------------------------------

class EventKind(StrEnum):
    USER_INPUT          = "user_input"
    SPEECH_TRANSCRIPT   = "speech_transcript"
    PERSON_DETECTED     = "person_detected"
    PERSON_LEFT         = "person_left"
    PROXIMITY_ALERT     = "proximity_alert"
    SYSTEM_FAULT        = "system_fault"
    BATTERY_LOW         = "battery_low"
    BATTERY_CRITICAL    = "battery_critical"
    OPERATOR_COMMAND    = "operator_command"
    ROUTINE_COMPLETE    = "routine_complete"
    ROUTINE_FAILED      = "routine_failed"
    IDLE_TIMEOUT        = "idle_timeout"
    CUSTOM              = "custom"


class EventSeverity(StrEnum):
    INFO     = "info"
    WARNING  = "warning"
    CRITICAL = "critical"


@dataclass
class SweetieBotEvent:
    """
    Normalised event.  All pipeline inputs become this before any
    state update or action recommendation is generated.
    """
    kind: EventKind
    severity: EventSeverity = EventSeverity.INFO
    source: str = "unknown"
    payload: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        d["severity"] = self.severity.value
        return d


@dataclass
class PipelineResult:
    """
    The result of processing one event through the pipeline.

    Includes:
    - The normalised event
    - State changes that were applied
    - Recommended action hints (NOT commands — pass through safety gate)
    """
    event: SweetieBotEvent
    state_changes: Dict[str, Any] = field(default_factory=dict)
    action_hints: List[str] = field(default_factory=list)
    safety_escalation: Optional[str] = None   # "safe" | "degraded" | "emergency" | None
    handled: bool = True
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event.to_dict(),
            "state_changes": self.state_changes,
            "action_hints": self.action_hints,
            "safety_escalation": self.safety_escalation,
            "handled": self.handled,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Event Pipeline
# ---------------------------------------------------------------------------

class EventPipeline:
    """
    Ingests, normalises, and processes events from all sources.

    Usage:
        pipeline = EventPipeline(state_manager=..., safety_gate=...)
        result = pipeline.ingest({"kind": "person_detected", "source": "camera"})

    The pipeline does NOT execute actions — it returns PipelineResult with
    ``action_hints`` that should be passed to the ExpressionCoordinator
    through the safety gate.
    """

    def __init__(
        self,
        *,
        state_manager: Any = None,
        safety_gate: Any = None,
        max_history: int = 100,
    ) -> None:
        self._state = state_manager
        self._gate  = safety_gate
        self._history: List[SweetieBotEvent] = []
        self._max_history = max_history
        self._handlers = {
            EventKind.USER_INPUT:        self._handle_user_input,
            EventKind.SPEECH_TRANSCRIPT: self._handle_speech_transcript,
            EventKind.PERSON_DETECTED:   self._handle_person_detected,
            EventKind.PERSON_LEFT:       self._handle_person_left,
            EventKind.PROXIMITY_ALERT:   self._handle_proximity_alert,
            EventKind.SYSTEM_FAULT:      self._handle_system_fault,
            EventKind.BATTERY_LOW:       self._handle_battery_low,
            EventKind.BATTERY_CRITICAL:  self._handle_battery_critical,
            EventKind.ROUTINE_COMPLETE:  self._handle_routine_complete,
            EventKind.ROUTINE_FAILED:    self._handle_routine_failed,
            EventKind.IDLE_TIMEOUT:      self._handle_idle_timeout,
            EventKind.OPERATOR_COMMAND:  self._handle_operator_command,
        }

    # ── Public API ─────────────────────────────────────────────────────

    def ingest(self, raw: Dict[str, Any]) -> PipelineResult:
        """
        Normalise a raw event dict and process it through the pipeline.
        Never raises — returns a result with handled=False on error.
        """
        try:
            event = self._normalise(raw)
            self._record(event)
            return self._process(event)
        except Exception as exc:
            log.error("EventPipeline.ingest error: %s", exc)
            fallback = SweetieBotEvent(
                kind=EventKind.CUSTOM,
                severity=EventSeverity.WARNING,
                source="pipeline_error",
                payload={"error": str(exc), "raw": raw},
            )
            return PipelineResult(event=fallback, handled=False, notes=[str(exc)])

    def ingest_event(self, event: SweetieBotEvent) -> PipelineResult:
        """Process a pre-built SweetieBotEvent directly."""
        self._record(event)
        return self._process(event)

    def recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in list(reversed(self._history))[:limit]]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "history_size": len(self._history),
            "last_event": self._history[-1].to_dict() if self._history else None,
        }

    # ── Normalisation ───────────────────────────────────────────────────

    def _normalise(self, raw: Dict[str, Any]) -> SweetieBotEvent:
        try:
            kind = EventKind(raw.get("kind", "custom"))
        except ValueError:
            kind = EventKind.CUSTOM

        try:
            severity = EventSeverity(raw.get("severity", "info"))
        except ValueError:
            severity = EventSeverity.INFO

        return SweetieBotEvent(
            kind=kind,
            severity=severity,
            source=str(raw.get("source", "unknown")),
            payload={k: v for k, v in raw.items() if k not in ("kind", "severity", "source")},
        )

    def _record(self, event: SweetieBotEvent) -> None:
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        log.debug("EventPipeline: %s from=%s", event.kind.value, event.source)

    def _process(self, event: SweetieBotEvent) -> PipelineResult:
        handler = self._handlers.get(event.kind, self._handle_custom)
        return handler(event)

    # ── Event handlers ──────────────────────────────────────────────────
    # Each handler returns a PipelineResult with state changes + hints.
    # Hints are strings like "greet_guest" that the caller can turn into
    # a CharacterResponse and pass through the safety gate.

    def _handle_user_input(self, event: SweetieBotEvent) -> PipelineResult:
        text = event.payload.get("text", "")
        changes = {}
        if self._state and text:
            changes["last_input"] = text
        return PipelineResult(
            event=event,
            state_changes=changes,
            action_hints=["process_dialogue"],
            notes=[f"user said: {text!r}"],
        )

    def _handle_speech_transcript(self, event: SweetieBotEvent) -> PipelineResult:
        text = event.payload.get("text", "")
        return PipelineResult(
            event=event,
            action_hints=["process_dialogue"],
            notes=[f"transcript: {text!r}"],
        )

    def _handle_person_detected(self, event: SweetieBotEvent) -> PipelineResult:
        person_id = event.payload.get("person_id", "guest")
        changes = {"focus_target": person_id}
        if self._state:
            try:
                self._state.set_focus(person_id)
            except Exception:
                pass
        return PipelineResult(
            event=event,
            state_changes=changes,
            action_hints=["greet_guest", "set_focus"],
            notes=[f"person detected: {person_id}"],
        )

    def _handle_person_left(self, event: SweetieBotEvent) -> PipelineResult:
        changes = {"focus_target": None}
        if self._state:
            try:
                self._state.set_focus(None)
            except Exception:
                pass
        return PipelineResult(
            event=event,
            state_changes=changes,
            action_hints=["return_to_idle"],
        )

    def _handle_proximity_alert(self, event: SweetieBotEvent) -> PipelineResult:
        """
        Something is too close — trigger safe mode.
        The gate will block all non-neutral routines.
        """
        distance = event.payload.get("distance_m", 0.0)
        self._escalate_safety("safe")
        return PipelineResult(
            event=event,
            state_changes={"safe_mode": True},
            action_hints=["return_to_neutral"],
            safety_escalation="safe",
            notes=[f"proximity alert: {distance}m"],
        )

    def _handle_system_fault(self, event: SweetieBotEvent) -> PipelineResult:
        fault = event.payload.get("fault_code", "unknown")
        severity = event.severity
        escalation = "emergency" if severity == EventSeverity.CRITICAL else "degraded"
        self._escalate_safety(escalation)
        return PipelineResult(
            event=event,
            state_changes={"degraded_mode": True},
            action_hints=["emergency_stop" if escalation == "emergency" else "return_to_neutral"],
            safety_escalation=escalation,
            notes=[f"system fault: {fault} severity={severity.value}"],
        )

    def _handle_battery_low(self, event: SweetieBotEvent) -> PipelineResult:
        pct = event.payload.get("battery_pct", 0)
        self._escalate_safety("degraded")
        return PipelineResult(
            event=event,
            state_changes={"degraded_mode": True},
            action_hints=["return_to_neutral"],
            safety_escalation="degraded",
            notes=[f"battery low: {pct}%"],
        )

    def _handle_battery_critical(self, event: SweetieBotEvent) -> PipelineResult:
        pct = event.payload.get("battery_pct", 0)
        self._escalate_safety("emergency")
        return PipelineResult(
            event=event,
            state_changes={"degraded_mode": True},
            action_hints=["emergency_stop"],
            safety_escalation="emergency",
            notes=[f"battery critical: {pct}%"],
        )

    def _handle_routine_complete(self, event: SweetieBotEvent) -> PipelineResult:
        routine_id = event.payload.get("routine_id")
        return PipelineResult(
            event=event,
            state_changes={"active_routine": None},
            action_hints=["return_to_idle"],
            notes=[f"routine complete: {routine_id}"],
        )

    def _handle_routine_failed(self, event: SweetieBotEvent) -> PipelineResult:
        routine_id = event.payload.get("routine_id")
        log.warning("EventPipeline: routine failed: %s", routine_id)
        return PipelineResult(
            event=event,
            state_changes={"active_routine": None},
            action_hints=["return_to_neutral"],
            notes=[f"routine failed: {routine_id}"],
        )

    def _handle_idle_timeout(self, event: SweetieBotEvent) -> PipelineResult:
        return PipelineResult(
            event=event,
            action_hints=["idle_cute"],
            notes=["idle timeout — suggest ambient idle routine"],
        )

    def _handle_operator_command(self, event: SweetieBotEvent) -> PipelineResult:
        command = event.payload.get("command", "")
        return PipelineResult(
            event=event,
            action_hints=[command] if command else [],
            notes=[f"operator command: {command}"],
        )

    def _handle_custom(self, event: SweetieBotEvent) -> PipelineResult:
        return PipelineResult(
            event=event,
            notes=[f"unhandled event kind: {event.kind.value}"],
            handled=False,
        )

    def _escalate_safety(self, mode: str) -> None:
        """Escalate safety gate mode if gate is available."""
        if self._gate is None:
            return
        try:
            from sweetiebot.integration.schemas import SafetyMode
            gate_mode = SafetyMode(mode)
            # Only escalate — never downgrade via event pipeline
            current = self._gate.safety_mode
            order = ["normal", "safe", "degraded", "emergency"]
            if order.index(mode) > order.index(current.value):
                self._gate.set_safety_mode(gate_mode)
                log.warning("EventPipeline: safety escalated to %s", mode)
        except Exception as exc:
            log.error("EventPipeline: safety escalation failed: %s", exc)

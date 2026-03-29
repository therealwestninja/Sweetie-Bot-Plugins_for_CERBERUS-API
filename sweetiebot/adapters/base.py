"""
sweetiebot.adapters.base
========================
Abstract base class for all robot adapters.

An adapter is the boundary between Sweetie-Bot's high-level intent system
and a specific robot hardware platform.  Sweetie-Bot NEVER calls an adapter
directly from character/dialogue logic — all adapter calls flow through the
safety gate, CERBERUS mapper, and expression coordinator first.

Implementors must honour the simulation-mode contract: when
``sim_mode=True``, every method must return a valid result dict without
touching real hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, List, Optional


class AdapterStatus(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTING   = "connecting"
    CONNECTED    = "connected"
    BUSY         = "busy"
    ERROR        = "error"
    SIM          = "sim"


class CommandStatus(StrEnum):
    OK       = "ok"
    SKIPPED  = "skipped"
    REJECTED = "rejected"
    ERROR    = "error"
    SIM      = "sim"


@dataclass
class AdapterCapabilities:
    """What this adapter/robot can actually do right now."""
    supported_routines: List[str] = field(default_factory=list)
    has_audio: bool = False
    has_accessories: bool = False
    has_tts: bool = False
    sim_mode: bool = True
    hardware_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "supported_routines": self.supported_routines,
            "has_audio": self.has_audio,
            "has_accessories": self.has_accessories,
            "has_tts": self.has_tts,
            "sim_mode": self.sim_mode,
            "hardware_id": self.hardware_id,
        }


@dataclass
class CommandResult:
    status: CommandStatus
    command: str
    detail: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "command": self.command,
            "detail": self.detail,
            "raw": self.raw,
        }


class AdapterBase:
    """
    Abstract base for all Sweetie-Bot hardware adapters.

    All methods that touch hardware must:
    1. Check self.sim_mode and return a sim result if True
    2. Never raise — return a CommandResult with status=ERROR on failure
    3. Never bypass the safety gate
    """

    adapter_id: str = "base.adapter"

    def __init__(self, *, sim_mode: bool = True) -> None:
        self.sim_mode = sim_mode
        self._status = AdapterStatus.SIM if sim_mode else AdapterStatus.DISCONNECTED
        self._last_result: Optional[CommandResult] = None

    def connect(self) -> Dict[str, Any]:
        raise NotImplementedError

    def disconnect(self) -> Dict[str, Any]:
        raise NotImplementedError

    def reconnect(self) -> Dict[str, Any]:
        self.disconnect()
        return self.connect()

    def health_check(self) -> Dict[str, Any]:
        raise NotImplementedError

    def capabilities(self) -> AdapterCapabilities:
        raise NotImplementedError

    def execute_motion(self, command: str, **kwargs: Any) -> CommandResult:
        raise NotImplementedError

    def set_accessory_state(self, scene_id: str) -> CommandResult:
        raise NotImplementedError

    def play_audio(self, cue_id: str, **kwargs: Any) -> CommandResult:
        raise NotImplementedError

    def emergency_stop(self) -> CommandResult:
        raise NotImplementedError

    @property
    def status(self) -> AdapterStatus:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status in (AdapterStatus.CONNECTED, AdapterStatus.BUSY, AdapterStatus.SIM)

    @property
    def last_result(self) -> Optional[CommandResult]:
        return self._last_result

    def _record(self, result: CommandResult) -> CommandResult:
        self._last_result = result
        return result


# Backward-compatible alias
class CerberusAdapterBase(AdapterBase):
    """Backward-compatible alias. Prefer AdapterBase directly."""

    def execute_routine(self, routine_id: str) -> Dict[str, Any]:
        return self.execute_motion(routine_id).to_dict()

    def set_emote(self, emote_id: str) -> Dict[str, Any]:
        return self.set_accessory_state(emote_id).to_dict()

    def speak(self, text: str) -> Dict[str, Any]:
        return self.play_audio("tts", text=text).to_dict()

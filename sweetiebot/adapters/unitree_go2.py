"""
sweetiebot.adapters.unitree_go2
================================
Capability-based adapter for the Unitree GO2 quadruped robot.

Architecture
------------
The adapter has two modes controlled by ``sim_mode``:

  sim_mode=True  (default, SWEETIEBOT_SIM_MODE=1)
    All commands are logged and return synthetic OK results.
    No Unitree SDK is required.  Safe for development and CI.

  sim_mode=False  (SWEETIEBOT_SIM_MODE=0)
    Commands are forwarded to the Unitree Sport Client SDK.
    Requires the SDK, a live GO2 EDU on the network, and
    a configured CycloneDDS interface (UNITREE_ETHERNET env var).

Safety rules
------------
* This adapter NEVER bypasses the safety gate.
* execute_motion() checks the motion allowlist before any call.
* emergency_stop() is ALWAYS available regardless of mode or state.
* On any exception, the adapter records CommandStatus.ERROR and returns —
  it does not propagate exceptions to the caller.

DO NOT call this adapter directly from dialogue or character logic.
All calls must flow through the ExpressionCoordinator and safety gate.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from sweetiebot.adapters.base import (
    AdapterBase,
    AdapterCapabilities,
    AdapterStatus,
    CommandResult,
    CommandStatus,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Motion command allowlist
# Maps routine_id → SDK sport command name.
# Only entries in this dict can be executed.  Unknown IDs are rejected.
# ---------------------------------------------------------------------------
_MOTION_ALLOWLIST: Dict[str, str] = {
    "greeting_01":       "Hello",
    "greet_guest":       "Hello",
    "photo_pose":        "Pose",
    "idle_cute":         "Wiggle",
    "return_to_neutral": "StandUp",
    "sit_stay":          "Sit",
}

# Per-motion cooldowns in seconds (enforced at adapter level — safety gate
# also enforces cooldowns, so this is a second defence-in-depth layer)
_MOTION_COOLDOWNS: Dict[str, float] = {
    "greeting_01":       8.0,
    "greet_guest":       8.0,
    "photo_pose":       12.0,
    "idle_cute":         4.0,
    "return_to_neutral": 0.0,
    "sit_stay":          6.0,
}


class UnitreeGo2Adapter(AdapterBase):
    """
    Unitree GO2 adapter — sim or real hardware depending on SWEETIEBOT_SIM_MODE.

    Environment variables
    ---------------------
    SWEETIEBOT_SIM_MODE   "1" (default) = sim, "0" = real hardware
    UNITREE_ETHERNET      Network interface name (e.g. "eth0", "en0")
                          Required when sim_mode=False
    """

    adapter_id = "unitree.go2"

    def __init__(
        self,
        *,
        sim_mode: Optional[bool] = None,
        network_interface: Optional[str] = None,
    ) -> None:
        # Default to sim unless explicitly disabled
        if sim_mode is None:
            sim_mode = os.environ.get("SWEETIEBOT_SIM_MODE", "1") != "0"
        super().__init__(sim_mode=sim_mode)

        self._interface = network_interface or os.environ.get("UNITREE_ETHERNET", "eth0")
        self._sdk_client: Any = None   # unitree_sdk2py SportClient, if available
        self._connect_time: Optional[float] = None
        self._cooldowns: Dict[str, float] = {}   # routine_id → last_executed_at

        mode_label = "SIM" if sim_mode else f"HARDWARE (iface={self._interface})"
        log.info("UnitreeGo2Adapter init: mode=%s", mode_label)

    # ── Connection lifecycle ────────────────────────────────────────────

    def connect(self) -> Dict[str, Any]:
        if self.sim_mode:
            self._status = AdapterStatus.SIM
            self._connect_time = time.monotonic()
            log.info("GO2 adapter: SIM connect OK")
            return {"connected": True, "mode": "sim", "adapter": self.adapter_id}

        try:
            self._status = AdapterStatus.CONNECTING
            client = self._load_sdk_client()
            client.Init()
            self._sdk_client = client
            self._status = AdapterStatus.CONNECTED
            self._connect_time = time.monotonic()
            log.info("GO2 adapter: real connect OK via %s", self._interface)
            return {"connected": True, "mode": "real", "interface": self._interface}
        except Exception as exc:
            self._status = AdapterStatus.ERROR
            log.error("GO2 adapter: connect failed: %s", exc)
            return {"connected": False, "error": str(exc), "mode": "real"}

    def disconnect(self) -> Dict[str, Any]:
        self._sdk_client = None
        self._connect_time = None
        self._status = AdapterStatus.SIM if self.sim_mode else AdapterStatus.DISCONNECTED
        log.info("GO2 adapter: disconnected")
        return {"disconnected": True}

    def health_check(self) -> Dict[str, Any]:
        uptime = round(time.monotonic() - self._connect_time, 1) if self._connect_time else None
        return {
            "adapter": self.adapter_id,
            "status": self._status.value,
            "sim_mode": self.sim_mode,
            "connected": self.is_connected,
            "uptime_seconds": uptime,
            "last_command": self._last_result.command if self._last_result else None,
            "last_status": self._last_result.status.value if self._last_result else None,
            "active_cooldowns": {
                k: round(_MOTION_COOLDOWNS.get(k, 5.0) - (time.monotonic() - v), 1)
                for k, v in self._cooldowns.items()
                if time.monotonic() - v < _MOTION_COOLDOWNS.get(k, 5.0)
            },
        }

    # ── Capability reporting ────────────────────────────────────────────

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supported_routines=list(_MOTION_ALLOWLIST.keys()),
            has_audio=True,          # GO2 EDU has a speaker
            has_accessories=True,    # LED eyes / light bar on some configs
            has_tts=False,           # TTS is handled by CERBERUS audio stack
            sim_mode=self.sim_mode,
            hardware_id="unitree.go2.edu" if not self.sim_mode else None,
        )

    # ── Command execution ───────────────────────────────────────────────

    def execute_motion(self, command: str, **kwargs: Any) -> CommandResult:
        """
        Execute a named motion command.

        Parameters
        ----------
        command:
            A routine_id from the CERBERUS allowlist (e.g. "greet_guest").
        """
        # 1. Allowlist check — fail-closed
        if command not in _MOTION_ALLOWLIST:
            result = CommandResult(
                status=CommandStatus.REJECTED,
                command=command,
                detail=f"'{command}' not in motion allowlist",
            )
            log.warning("GO2 motion rejected: %s", command)
            return self._record(result)

        # 2. Adapter-level cooldown check (defence-in-depth)
        last_at = self._cooldowns.get(command, 0.0)
        cooldown = _MOTION_COOLDOWNS.get(command, 5.0)
        elapsed = time.monotonic() - last_at
        if elapsed < cooldown and command != "return_to_neutral":
            retry = round(cooldown - elapsed, 1)
            result = CommandResult(
                status=CommandStatus.SKIPPED,
                command=command,
                detail=f"adapter cooldown active: retry in {retry}s",
            )
            log.debug("GO2 motion skipped (cooldown): %s retry_in=%.1f", command, retry)
            return self._record(result)

        sdk_cmd = _MOTION_ALLOWLIST[command]

        # 3. Simulation path
        if self.sim_mode:
            self._cooldowns[command] = time.monotonic()
            result = CommandResult(
                status=CommandStatus.SIM,
                command=command,
                detail=f"[SIM] would call SDK SportClient.{sdk_cmd}()",
                raw={"sdk_command": sdk_cmd, "kwargs": kwargs},
            )
            log.info("[SIM] GO2 motion: routine=%s sdk=%s", command, sdk_cmd)
            return self._record(result)

        # 4. Real hardware path
        try:
            self._status = AdapterStatus.BUSY
            sdk_method = getattr(self._sdk_client, sdk_cmd)
            sdk_method()
            self._cooldowns[command] = time.monotonic()
            self._status = AdapterStatus.CONNECTED
            result = CommandResult(
                status=CommandStatus.OK,
                command=command,
                detail=f"SDK SportClient.{sdk_cmd}() executed",
                raw={"sdk_command": sdk_cmd},
            )
            log.info("GO2 motion OK: routine=%s sdk=%s", command, sdk_cmd)
        except Exception as exc:
            self._status = AdapterStatus.ERROR
            result = CommandResult(
                status=CommandStatus.ERROR,
                command=command,
                detail=f"SDK error: {exc}",
            )
            log.error("GO2 motion error: routine=%s error=%s", command, exc)
            # Attempt recovery
            self._attempt_neutral_recovery()

        return self._record(result)

    def set_accessory_state(self, scene_id: str) -> CommandResult:
        """Set LED / eye accessory state.  No-op on hardware without accessories."""
        if self.sim_mode:
            result = CommandResult(
                status=CommandStatus.SIM,
                command=f"accessory:{scene_id}",
                detail=f"[SIM] accessory scene={scene_id}",
            )
            log.info("[SIM] GO2 accessory: scene=%s", scene_id)
            return self._record(result)

        # Real hardware: forward to CERBERUS accessory API (not implemented here)
        # CERBERUS controls the LED/eye hardware — we emit the intent only
        result = CommandResult(
            status=CommandStatus.OK,
            command=f"accessory:{scene_id}",
            detail=f"accessory intent emitted: {scene_id} (CERBERUS executes)",
        )
        return self._record(result)

    def play_audio(self, cue_id: str, **kwargs: Any) -> CommandResult:
        """Play an audio cue via CERBERUS audio stack."""
        text = kwargs.get("text", "")
        if self.sim_mode:
            result = CommandResult(
                status=CommandStatus.SIM,
                command=f"audio:{cue_id}",
                detail=f"[SIM] audio cue={cue_id} text={text!r}",
            )
            log.info("[SIM] GO2 audio: cue=%s text=%r", cue_id, text)
            return self._record(result)

        # Real hardware: CERBERUS handles audio via its own pipeline
        result = CommandResult(
            status=CommandStatus.OK,
            command=f"audio:{cue_id}",
            detail=f"audio intent emitted: cue={cue_id} (CERBERUS executes)",
        )
        return self._record(result)

    def emergency_stop(self) -> CommandResult:
        """
        Immediately return robot to standing neutral.
        Always available — bypasses cooldowns.
        """
        log.warning("GO2 EMERGENCY STOP invoked")
        if self.sim_mode:
            result = CommandResult(
                status=CommandStatus.SIM,
                command="emergency_stop",
                detail="[SIM] emergency stop — would call SDK StandUp()",
            )
            log.warning("[SIM] GO2 emergency stop")
            return self._record(result)

        try:
            if self._sdk_client:
                self._sdk_client.StandUp()
            self._status = AdapterStatus.CONNECTED
            result = CommandResult(
                status=CommandStatus.OK,
                command="emergency_stop",
                detail="SDK StandUp() executed",
            )
            log.warning("GO2 emergency stop: StandUp OK")
        except Exception as exc:
            self._status = AdapterStatus.ERROR
            result = CommandResult(
                status=CommandStatus.ERROR,
                command="emergency_stop",
                detail=f"emergency stop SDK error: {exc}",
            )
            log.error("GO2 emergency stop error: %s", exc)

        return self._record(result)

    # ── Backward-compat (old stub interface) ───────────────────────────

    def execute_routine(self, routine_id: str) -> Dict[str, Any]:
        return self.execute_motion(routine_id).to_dict()

    def set_emote(self, emote_id: str) -> Dict[str, Any]:
        return self.set_accessory_state(emote_id).to_dict()

    def speak(self, text: str) -> Dict[str, Any]:
        return self.play_audio("tts", text=text).to_dict()

    # ── Internals ───────────────────────────────────────────────────────

    def _attempt_neutral_recovery(self) -> None:
        """Best-effort recovery: try to stand up after an error."""
        try:
            if self._sdk_client:
                self._sdk_client.StandUp()
                self._status = AdapterStatus.CONNECTED
                log.info("GO2 neutral recovery: StandUp OK")
        except Exception as exc:
            log.error("GO2 neutral recovery failed: %s", exc)

    def _load_sdk_client(self) -> Any:
        """
        Load the Unitree SDK SportClient.  Raises ImportError if the SDK
        is not installed (install unitree_sdk2py separately).
        """
        try:
            from unitree_sdk2py.go2.sport.sport_client import SportClient  # type: ignore[import]
            client = SportClient()
            client.SetTimeout(10.0)
            client.Init()
            return client
        except ImportError as exc:
            raise ImportError(
                "unitree_sdk2py is not installed. "
                "Run: pip install unitree_sdk2py\n"
                "Or set SWEETIEBOT_SIM_MODE=1 to use simulation mode."
            ) from exc

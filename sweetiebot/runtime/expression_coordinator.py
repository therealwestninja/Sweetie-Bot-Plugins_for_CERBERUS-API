"""
sweetiebot.runtime.expression_coordinator
==========================================
Coordinates the simultaneous expression channels of Sweetie-Bot:

  - speech (text-to-speech)
  - motion (routines on the robot)
  - emote  (facial/body animation layer)
  - accessory (LED eyes, light bar)

Problems this solves
--------------------
Without coordination, callers could fire a motion and an emote
simultaneously, causing the robot to try two conflicting actions.
This coordinator serialises physical actions and prevents overlap.

Design
------
* Each channel has an independent lock tracked by a simple flag.
* A new request to a locked channel is queued or rejected depending
  on interrupt_ok.
* If any channel throws, the coordinator calls return_to_neutral()
  so the robot always ends in a known safe state.
* No hardware is called here — the coordinator calls the adapter,
  which decides whether to sim or execute.

Thread safety: this coordinator is single-threaded (event loop style).
For async FastAPI use, wrap calls with asyncio.to_thread() if needed.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ExpressionResult:
    ok: bool
    channels: Dict[str, Any] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    interrupted: List[str] = field(default_factory=list)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "channels": self.channels,
            "skipped": self.skipped,
            "errors": self.errors,
            "interrupted": self.interrupted,
            "duration_ms": round(self.duration_ms, 2),
        }


# ---------------------------------------------------------------------------
# Channel lock tracker
# ---------------------------------------------------------------------------

@dataclass
class _ChannelState:
    name: str
    locked: bool = False
    locked_since: Optional[float] = None
    last_command: Optional[str] = None

    def acquire(self, command: str) -> bool:
        if self.locked:
            return False
        self.locked = True
        self.locked_since = time.monotonic()
        self.last_command = command
        return True

    def release(self) -> None:
        self.locked = False
        self.locked_since = None

    def force_release(self) -> str:
        prev = self.last_command or "unknown"
        self.release()
        return prev


# ---------------------------------------------------------------------------
# ExpressionCoordinator
# ---------------------------------------------------------------------------

class ExpressionCoordinator:
    """
    Coordinates speech + motion + emote + accessory into a single,
    conflict-free expression.

    Parameters
    ----------
    adapter:
        A connected ``AdapterBase`` (or subclass) instance.  All physical
        commands are delegated to the adapter.
    default_neutral_emote:
        The emote_id to set when returning to neutral.
    default_neutral_accessory:
        The accessory scene_id to set when returning to neutral.
    """

    def __init__(
        self,
        adapter: Any,
        *,
        default_neutral_emote: str = "calm_neutral",
        default_neutral_accessory: str = "eyes_neutral",
    ) -> None:
        self._adapter = adapter
        self._neutral_emote = default_neutral_emote
        self._neutral_accessory = default_neutral_accessory

        # One state object per channel
        self._motion    = _ChannelState("motion")
        self._emote     = _ChannelState("emote")
        self._accessory = _ChannelState("accessory")
        self._speech    = _ChannelState("speech")

        self._last_expression: Optional[ExpressionResult] = None

    # ── Public API ─────────────────────────────────────────────────────

    def express(
        self,
        *,
        speech: Optional[str] = None,
        motion: Optional[str] = None,
        emote: Optional[str] = None,
        accessory: Optional[str] = None,
        interrupt_motion: bool = False,
        interrupt_emote: bool = True,
    ) -> ExpressionResult:
        """
        Execute a coordinated expression across all channels.

        Parameters
        ----------
        speech:
            Text to speak (delegated to adapter.play_audio / TTS).
        motion:
            routine_id to execute on the robot.
        emote:
            emote_id to apply (animation / expression layer).
        accessory:
            accessory scene_id to set.
        interrupt_motion:
            If True and motion is locked, cancel current motion first.
            Defaults to False (safe default — don't interrupt motion).
        interrupt_emote:
            If True and emote is locked, cancel current emote first.
            Defaults to True (emotes are cheap to interrupt).

        Returns
        -------
        ExpressionResult with per-channel outcomes.
        """
        t0 = time.monotonic()
        result = ExpressionResult(ok=True)

        try:
            # 1. Motion channel
            if motion is not None:
                self._run_motion(motion, interrupt=interrupt_motion, result=result)

            # 2. Emote channel (usually concurrent with motion)
            if emote is not None:
                self._run_emote(emote, interrupt=interrupt_emote, result=result)

            # 3. Accessory (instant — no lock needed, no overlap risk)
            if accessory is not None:
                self._run_accessory(accessory, result=result)

            # 4. Speech (non-blocking intent — TTS is async in CERBERUS)
            if speech is not None:
                self._run_speech(speech, result=result)

        except Exception as exc:
            result.ok = False
            result.errors.append(f"coordinator exception: {exc}")
            log.error("ExpressionCoordinator unhandled error: %s", exc)
            self._safe_return_to_neutral(result)
        finally:
            result.duration_ms = (time.monotonic() - t0) * 1000

        self._last_expression = result
        return result

    def return_to_neutral(self) -> ExpressionResult:
        """
        Immediately clear all locks and return robot to neutral state.
        Always safe to call — never raises.
        """
        result = ExpressionResult(ok=True)
        t0 = time.monotonic()

        # Force-release all channels
        for ch in (self._motion, self._emote, self._accessory, self._speech):
            if ch.locked:
                prev = ch.force_release()
                result.interrupted.append(f"{ch.name}:{prev}")

        try:
            r = self._adapter.execute_motion("return_to_neutral")
            result.channels["motion"] = r.to_dict() if hasattr(r, "to_dict") else r
        except Exception as exc:
            result.errors.append(f"neutral motion error: {exc}")

        try:
            r = self._adapter.set_accessory_state(self._neutral_accessory)
            result.channels["accessory"] = r.to_dict() if hasattr(r, "to_dict") else r
        except Exception as exc:
            result.errors.append(f"neutral accessory error: {exc}")

        result.duration_ms = (time.monotonic() - t0) * 1000
        result.ok = not result.errors
        self._last_expression = result
        log.info("ExpressionCoordinator: returned to neutral interrupted=%s", result.interrupted)
        return result

    def interrupt(self, channels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Release locks on specified channels (default: all).
        Does NOT command the robot — just unblocks the coordinator.
        """
        targets = channels or ["motion", "emote", "accessory", "speech"]
        released = []
        for name in targets:
            ch = self._get_channel(name)
            if ch and ch.locked:
                prev = ch.force_release()
                released.append(f"{name}:{prev}")
        return {"released": released}

    def snapshot(self) -> Dict[str, Any]:
        return {
            "channels": {
                ch.name: {
                    "locked": ch.locked,
                    "last_command": ch.last_command,
                    "locked_since": round(time.monotonic() - ch.locked_since, 2) if ch.locked_since else None,
                }
                for ch in [self._motion, self._emote, self._accessory, self._speech]
            },
            "last_expression": self._last_expression.to_dict() if self._last_expression else None,
        }

    # ── Internal helpers ────────────────────────────────────────────────

    def _run_motion(self, motion: str, interrupt: bool, result: ExpressionResult) -> None:
        if self._motion.locked:
            if interrupt:
                prev = self._motion.force_release()
                result.interrupted.append(f"motion:{prev}")
                log.info("ExpressionCoordinator: motion interrupted (was %s)", prev)
            else:
                result.skipped.append(f"motion:{motion}")
                log.debug("ExpressionCoordinator: motion skipped (locked by %s)", self._motion.last_command)
                return

        if self._motion.acquire(motion):
            try:
                r = self._adapter.execute_motion(motion)
                result.channels["motion"] = r.to_dict() if hasattr(r, "to_dict") else r
                log.info("ExpressionCoordinator: motion=%s status=%s", motion, getattr(r, "status", "?"))
            except Exception as exc:
                result.errors.append(f"motion error: {exc}")
                result.ok = False
                log.error("ExpressionCoordinator: motion error motion=%s exc=%s", motion, exc)
            finally:
                self._motion.release()

    def _run_emote(self, emote: str, interrupt: bool, result: ExpressionResult) -> None:
        if self._emote.locked and not interrupt:
            result.skipped.append(f"emote:{emote}")
            return
        if self._emote.locked:
            result.interrupted.append(f"emote:{self._emote.force_release()}")

        if self._emote.acquire(emote):
            try:
                r = self._adapter.set_accessory_state(emote)
                result.channels["emote"] = r.to_dict() if hasattr(r, "to_dict") else r
            except Exception as exc:
                result.errors.append(f"emote error: {exc}")
            finally:
                self._emote.release()

    def _run_accessory(self, accessory: str, result: ExpressionResult) -> None:
        try:
            r = self._adapter.set_accessory_state(accessory)
            result.channels["accessory"] = r.to_dict() if hasattr(r, "to_dict") else r
        except Exception as exc:
            result.errors.append(f"accessory error: {exc}")

    def _run_speech(self, speech: str, result: ExpressionResult) -> None:
        try:
            r = self._adapter.play_audio("tts", text=speech)
            result.channels["speech"] = r.to_dict() if hasattr(r, "to_dict") else r
        except Exception as exc:
            result.errors.append(f"speech error: {exc}")

    def _safe_return_to_neutral(self, result: ExpressionResult) -> None:
        """Called on unexpected error — never raises."""
        try:
            self._adapter.execute_motion("return_to_neutral")
            result.channels["emergency_neutral"] = {"status": "ok"}
        except Exception as exc:
            result.errors.append(f"emergency neutral failed: {exc}")

    def _get_channel(self, name: str) -> Optional[_ChannelState]:
        return {
            "motion": self._motion,
            "emote": self._emote,
            "accessory": self._accessory,
            "speech": self._speech,
        }.get(name)

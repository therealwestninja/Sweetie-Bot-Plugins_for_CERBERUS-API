"""
sweetiebot.observability.structured_log
=========================================
Lightweight structured logging layer for Sweetie-Bot.

Goals
-----
* Every significant decision is logged as a JSON-serialisable dict.
* ``DecisionLedger`` keeps a bounded in-memory record of the last N decisions
  so the ``/debug/last-decision`` endpoint can always answer immediately.
* No external dependencies (no Langfuse, no OpenTelemetry SDK).
  If you want to add those later, this module is the single place to do it.

Usage
-----
    from sweetiebot.observability.structured_log import get_logger, DecisionLedger

    log = get_logger("integration")
    ledger = DecisionLedger()          # one per runtime (singleton pattern below)

    ledger.record("integration.plan", {"approved": True, "plan_id": "..."})
    log.decision("plan created", context={"plan_id": "..."})
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional


# ---------------------------------------------------------------------------
# Structured formatter — emits one JSON line per log record
# ---------------------------------------------------------------------------

class JSONLineFormatter(logging.Formatter):
    """Formats log records as single-line JSON for structured log sinks."""

    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Merge any extra fields attached to the record
        for key, value in record.__dict__.items():
            if key.startswith("ctx_"):
                base[key[4:]] = value  # strip ctx_ prefix
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(base, default=str)


def _configure_root_logger(level: int = logging.INFO) -> None:
    """Configure the root logger with JSON output if not already configured."""
    root = logging.getLogger()
    if root.handlers:
        return  # already configured by the host application
    handler = logging.StreamHandler()
    handler.setFormatter(JSONLineFormatter())
    root.addHandler(handler)
    root.setLevel(level)


_configure_root_logger()


# ---------------------------------------------------------------------------
# SweetieBotLogger — thin wrapper with a .decision() helper
# ---------------------------------------------------------------------------

class SweetieBotLogger:
    """
    Wraps a standard ``logging.Logger`` and adds a ``decision()`` method that
    emits a structured log record with a mandatory ``context`` dict attached.
    """

    def __init__(self, name: str) -> None:
        self._log = logging.getLogger(name)

    def decision(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        level: str = "info",
    ) -> None:
        lvl = getattr(logging, level.upper(), logging.INFO)
        extra = {f"ctx_{k}": v for k, v in (context or {}).items()}
        self._log.log(lvl, message, extra=extra)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.error(msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.debug(msg, *args, **kwargs)


def get_logger(name: str) -> SweetieBotLogger:
    return SweetieBotLogger(f"sweetiebot.{name}")


# ---------------------------------------------------------------------------
# Decision Ledger — in-memory record for /debug/last-decision
# ---------------------------------------------------------------------------

class DecisionEntry:
    """One recorded decision."""

    __slots__ = ("decision_type", "timestamp", "context", "elapsed_ms")

    def __init__(
        self,
        decision_type: str,
        context: Dict[str, Any],
        elapsed_ms: Optional[float] = None,
    ) -> None:
        self.decision_type = decision_type
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.context = context
        self.elapsed_ms = elapsed_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_type": self.decision_type,
            "timestamp": self.timestamp,
            "elapsed_ms": self.elapsed_ms,
            "context": self.context,
        }


class DecisionLedger:
    """
    Bounded in-memory ledger of recent decisions.

    One ``DecisionLedger`` should be created per runtime and shared across
    all integration components. The ``/debug/last-decision`` endpoint reads
    from it directly.
    """

    def __init__(self, capacity: int = 100) -> None:
        self._capacity = capacity
        self._entries: Deque[DecisionEntry] = deque(maxlen=capacity)

    def record(
        self,
        decision_type: str,
        context: Dict[str, Any],
        *,
        elapsed_ms: Optional[float] = None,
    ) -> DecisionEntry:
        entry = DecisionEntry(decision_type, context, elapsed_ms)
        self._entries.append(entry)
        return entry

    def last(self) -> Optional[Dict[str, Any]]:
        if not self._entries:
            return None
        return self._entries[-1].to_dict()

    def recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        entries = list(self._entries)
        return [e.to_dict() for e in reversed(entries[-limit:])]

    def by_type(self, decision_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        matching = [e for e in self._entries if e.decision_type == decision_type]
        return [e.to_dict() for e in reversed(matching[-limit:])]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "capacity": self._capacity,
            "size": len(self._entries),
            "last": self.last(),
        }


# ---------------------------------------------------------------------------
# Module-level singleton (convenience — import and use directly)
# ---------------------------------------------------------------------------

_ledger: Optional[DecisionLedger] = None


def get_ledger() -> DecisionLedger:
    """Return the module-level ``DecisionLedger`` singleton."""
    global _ledger
    if _ledger is None:
        _ledger = DecisionLedger(capacity=100)
    return _ledger

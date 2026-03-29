from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

_DEFAULT_FORMAT = "%(message)s"


def _json_default(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "__dict__"):
        return value.__dict__
    return str(value)


@dataclass(slots=True)
class Event:
    event_type: str
    message: str
    level: str = "INFO"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=_json_default, sort_keys=True)


def get_logger(name: str = "sweetiebot", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


class EventLogger:
    """Minimal structured logger for runtime and plugin events."""

    def __init__(self, name: str = "sweetiebot", level: int = logging.INFO) -> None:
        self._logger = get_logger(name, level=level)

    def emit(
        self,
        event_type: str,
        message: str,
        *,
        level: str = "INFO",
        data: Mapping[str, Any] | None = None,
    ) -> None:
        event = Event(
            event_type=event_type,
            message=message,
            level=level.upper(),
            data=dict(data or {}),
        )
        log_level = getattr(logging, event.level, logging.INFO)
        self._logger.log(log_level, event.to_json())

    def plugin_loaded(self, plugin_id: str, plugin_type: str, *, built_in: bool = False) -> None:
        self.emit(
            "plugin.loaded",
            f"Loaded plugin {plugin_id}",
            data={"plugin_id": plugin_id, "plugin_type": plugin_type, "built_in": built_in},
        )

    def dialogue_generated(self, *, intent: str, emote_id: str | None, routine_id: str | None) -> None:
        self.emit(
            "dialogue.generated",
            "Dialogue reply generated",
            data={"intent": intent, "emote_id": emote_id, "routine_id": routine_id},
        )

    def validation_failed(self, source: str, reason: str, *, payload: Any | None = None) -> None:
        self.emit(
            "validation.failed",
            f"Validation failed for {source}",
            level="WARNING",
            data={"source": source, "reason": reason, "payload": payload},
        )

    def runtime_state_changed(self, state_name: str, old: Any, new: Any) -> None:
        self.emit(
            "runtime.state_changed",
            f"{state_name} changed",
            data={"state_name": state_name, "old": old, "new": new},
        )

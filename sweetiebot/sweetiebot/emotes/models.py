from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EmoteSelection:
    emote_id: str
    reason: str
    intensity: float = 0.75
    source: str = "emote_mapper"
    confidence: float = 0.8
    metadata: Dict[str, Any] = field(default_factory=dict)
    selection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

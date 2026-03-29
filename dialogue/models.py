from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DialogueResponse:
    spoken_text: str
    intent: str = "reply"
    emote_id: str = "calm_neutral"
    routine_id: Optional[str] = None
    confidence: float = 0.8
    source: str = "dialogue_provider"
    metadata: Dict[str, Any] = field(default_factory=dict)
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

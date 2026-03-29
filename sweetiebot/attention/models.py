from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AttentionSuggestion:
    target: Optional[str]
    reason: str
    priority: str = "medium"
    confidence: float = 0.75
    source: str = "attention_strategy"
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

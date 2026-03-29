from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryRecord:
    kind: str
    content: str
    source: str = "runtime"
    tags: List[str] = field(default_factory=list)
    scope: str = "session"
    importance: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryQuery:
    text: Optional[str] = None
    kind: Optional[str] = None
    scope: Optional[str] = None
    limit: int = 10

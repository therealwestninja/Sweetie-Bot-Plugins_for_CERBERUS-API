from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CharacterEvent:
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

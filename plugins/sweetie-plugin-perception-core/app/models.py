from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Detection(BaseModel):
    label: str
    id: Optional[str] = None
    confidence: float = 0.0
    position: Dict[str, float] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

class IngestRequest(BaseModel):
    source: str = "unknown"
    detections: List[Detection] = Field(default_factory=list)
    scene: Dict[str, Any] = Field(default_factory=dict)

class IdRequest(BaseModel):
    track_id: str

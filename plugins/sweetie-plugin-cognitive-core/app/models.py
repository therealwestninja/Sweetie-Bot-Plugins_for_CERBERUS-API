from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GenericEvent(BaseModel):
    topic: str
    source: str = "unknown"
    payload: Dict[str, Any] = Field(default_factory=dict)

class PerceiveEventRequest(BaseModel):
    event: GenericEvent

class EvaluateContextRequest(BaseModel):
    context: Dict[str, Any] = Field(default_factory=dict)

class ChooseActionRequest(BaseModel):
    context: Dict[str, Any] = Field(default_factory=dict)

class SetStateRequest(BaseModel):
    mood: Optional[str] = None
    curiosity: Optional[float] = None
    sociability: Optional[float] = None
    caution: Optional[float] = None
    battery_bias: Optional[float] = None
    notes: List[str] = Field(default_factory=list)

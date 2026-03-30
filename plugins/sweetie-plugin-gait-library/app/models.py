from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class ProfileRequest(BaseModel):
    profile: str

class GaitRequest(BaseModel):
    profile: str
    gait: str

class GetGaitRequest(BaseModel):
    profile: Optional[str] = None
    gait: str

class AdaptCommandRequest(BaseModel):
    profile: Optional[str] = None
    gait: Optional[str] = None
    command: Dict[str, Any] = Field(default_factory=dict)

class PreviewSequenceRequest(BaseModel):
    profile: Optional[str] = None
    gait: Optional[str] = None
    seconds: float = 3.0

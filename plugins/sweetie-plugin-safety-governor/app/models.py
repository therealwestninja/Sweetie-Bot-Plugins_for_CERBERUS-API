from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field

class EvaluateActionRequest(BaseModel):
    action: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

class SetPolicyRequest(BaseModel):
    max_speed_mps: float | None = None
    min_human_distance_m: float | None = None
    low_battery_threshold: float | None = None
    restricted_zones: List[Dict[str, float]] = Field(default_factory=list)

class ReportContextRequest(BaseModel):
    context: Dict[str, Any] = Field(default_factory=dict)

from __future__ import annotations
from typing import Dict, List
from pydantic import BaseModel, Field

class Point(BaseModel):
    x: float
    y: float

class SetPositionRequest(BaseModel):
    position: Point

class PlanToPointRequest(BaseModel):
    goal: Point

class PlanToLocationRequest(BaseModel):
    name: str
    locations: Dict[str, Dict[str, float]] = Field(default_factory=dict)

class FollowRouteRequest(BaseModel):
    route_id: str

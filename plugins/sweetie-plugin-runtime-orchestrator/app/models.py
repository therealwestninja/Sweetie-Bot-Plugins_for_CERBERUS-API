from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Point2D(BaseModel):
    x: float
    y: float

class FollowObjectRequest(BaseModel):
    object_id: str
    standoff_m: float = 0.75

class PatrolMissionRequest(BaseModel):
    waypoints: List[Point2D] = Field(default_factory=list)
    loop: bool = False

class RegisterRoutesRequest(BaseModel):
    registry_url: Optional[str] = None
    world_model_url: Optional[str] = None
    nav_url: Optional[str] = None
    mission_url: Optional[str] = None
    sim_url: Optional[str] = None

class ChainExecuteRequest(BaseModel):
    chain_name: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class SimulateChainStep(BaseModel):
    observation: Dict[str, Any] = Field(default_factory=dict)
    action: Dict[str, Any] = Field(default_factory=dict)
    reward: float = 0.0
    done: bool = False
    notes: List[str] = Field(default_factory=list)

class SimulateChainRequest(BaseModel):
    episode_name: str
    scenario: str = "runtime-orchestrator"
    steps: List[SimulateChainStep] = Field(default_factory=list)

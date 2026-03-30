from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field

class PublishEventRequest(BaseModel):
    topic: str
    source: str = "unknown"
    payload: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

class SubscribeRequest(BaseModel):
    subscriber_id: str
    topics: List[str] = Field(default_factory=list)

class UnsubscribeRequest(BaseModel):
    subscriber_id: str

class PollRequest(BaseModel):
    subscriber_id: str
    limit: int = 10

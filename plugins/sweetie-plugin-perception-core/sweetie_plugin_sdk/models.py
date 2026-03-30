from typing import Any, Dict
from pydantic import BaseModel, Field
class ExecuteRequest(BaseModel):
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
class PluginResponse(BaseModel):
    ok: bool = True
    plugin: str
    action: str
    data: Dict[str, Any] = Field(default_factory=dict)

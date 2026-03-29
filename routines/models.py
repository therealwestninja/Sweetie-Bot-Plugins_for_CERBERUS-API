from __future__ import annotations

from pydantic import BaseModel, Field


class RoutineStep(BaseModel):
    action: str = Field(min_length=1)
    value: str | int | None = None


class RoutineModel(BaseModel):
    routine_id: str = Field(min_length=1)
    summary: str = Field(default="")
    interruptible: bool = Field(default=True)
    steps: list[RoutineStep] = Field(default_factory=list)

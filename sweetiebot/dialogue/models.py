from __future__ import annotations

from pydantic import BaseModel, Field


class DialogueReply(BaseModel):
    intent: str = Field(default="chat")
    spoken_text: str = Field(default="")
    emote_id: str | None = None
    routine_id: str | None = None
    accessory_scene_id: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    fallback: bool = False

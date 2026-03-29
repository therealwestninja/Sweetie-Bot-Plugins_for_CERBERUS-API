from __future__ import annotations

from pydantic import BaseModel, Field


class PersonaModel(BaseModel):
    persona_id: str = Field(default="sweetiebot.core", min_length=1)
    display_name: str = Field(default="Sweetie Bot", min_length=1)
    speaking_style: str = Field(default="warm, cute, concise")
    default_emote: str = Field(default="calm_neutral")
    fallback_lines: list[str] = Field(default_factory=lambda: ["Eep! Let me try that again."])

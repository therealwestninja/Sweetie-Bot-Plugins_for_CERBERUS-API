from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class DialogueProviderResult:
    text: str
    provider: str
    model: str
    raw: dict[str, Any] | None = None


class DialogueProvider(Protocol):
    def is_configured(self) -> bool: ...
    def generate_reply(self, *, system_prompt: str, user_text: str) -> DialogueProviderResult: ...
    def describe(self) -> dict[str, Any]: ...


class LocalDialogueProvider:
    def __init__(self, *, dialogue_manager) -> None:
        self.dialogue_manager = dialogue_manager

    def is_configured(self) -> bool:
        return True

    def generate_reply(self, *, system_prompt: str, user_text: str) -> DialogueProviderResult:
        del system_prompt
        reply = self.dialogue_manager.reply_for(user_text)
        return DialogueProviderResult(
            text=reply.text,
            provider="local",
            model="rule-based-local",
            raw=reply.to_dict(),
        )

    def describe(self) -> dict[str, Any]:
        return {"provider": "local", "configured": True, "model": "rule-based-local"}

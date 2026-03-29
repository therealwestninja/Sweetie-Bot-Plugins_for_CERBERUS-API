from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx


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


class OpenAIResponsesProvider:
    def __init__(self, *, api_key: str, model: str, base_url: str = "https://api.openai.com/v1", transport: httpx.BaseTransport | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.transport = transport

    def generate_reply(self, *, system_prompt: str, user_text: str) -> DialogueProviderResult:
        with httpx.Client(transport=self.transport) as client:
            response = client.post(
                f"{self.base_url}/responses",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}]},
            )
            data = response.json()
        return DialogueProviderResult(text=data.get("output_text", ""), provider="openai", model=self.model, raw=data)


class AnthropicMessagesProvider:
    def __init__(self, *, api_key: str, model: str, base_url: str = "https://api.anthropic.com", transport: httpx.BaseTransport | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.transport = transport

    def generate_reply(self, *, system_prompt: str, user_text: str) -> DialogueProviderResult:
        with httpx.Client(transport=self.transport) as client:
            response = client.post(
                f"{self.base_url}/v1/messages",
                headers={"x-api-key": self.api_key},
                json={"model": self.model, "system": system_prompt, "messages": [{"role": "user", "content": user_text}]},
            )
            data = response.json()
        text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        return DialogueProviderResult(text=text, provider="anthropic", model=self.model, raw=data)

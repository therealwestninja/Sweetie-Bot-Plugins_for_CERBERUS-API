from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx


@dataclass
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
            provider='local',
            model='rule-based-local',
            raw={'intent': reply.intent.value, 'emote_id': reply.emote_id},
        )

    def describe(self) -> dict[str, Any]:
        return {'provider': 'local', 'configured': True, 'model': 'rule-based-local'}


class OpenAIResponsesProvider:
    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        base_url: str,
        timeout_s: float = 20.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.timeout_s = timeout_s
        self.transport = transport

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_reply(self, *, system_prompt: str, user_text: str) -> DialogueProviderResult:
        if not self.api_key:
            raise RuntimeError('OPENAI_API_KEY is not configured')
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': self.model,
            'input': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_text},
            ],
        }
        with httpx.Client(timeout=self.timeout_s, transport=self.transport) as client:
            response = client.post(
                f'{self.base_url}/responses',
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        text = data.get('output_text') or _extract_openai_text(data)
        return DialogueProviderResult(
            text=text.strip(),
            provider='openai',
            model=self.model,
            raw=data,
        )

    def describe(self) -> dict[str, Any]:
        return {'provider': 'openai', 'configured': self.is_configured(), 'model': self.model}


class AnthropicMessagesProvider:
    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        base_url: str,
        timeout_s: float = 20.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.timeout_s = timeout_s
        self.transport = transport

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_reply(self, *, system_prompt: str, user_text: str) -> DialogueProviderResult:
        if not self.api_key:
            raise RuntimeError('ANTHROPIC_API_KEY is not configured')
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        }
        payload = {
            'model': self.model,
            'max_tokens': 300,
            'system': system_prompt,
            'messages': [{'role': 'user', 'content': user_text}],
        }
        with httpx.Client(timeout=self.timeout_s, transport=self.transport) as client:
            response = client.post(
                f'{self.base_url}/v1/messages',
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        text = _extract_anthropic_text(data)
        return DialogueProviderResult(
            text=text.strip(),
            provider='anthropic',
            model=self.model,
            raw=data,
        )

    def describe(self) -> dict[str, Any]:
        return {
            'provider': 'anthropic',
            'configured': self.is_configured(),
            'model': self.model,
        }


def _extract_openai_text(data: dict[str, Any]) -> str:
    for item in data.get('output', []):
        for content in item.get('content', []):
            if content.get('type') == 'output_text':
                return content.get('text', '')
            if content.get('type') == 'text':
                return content.get('text', '')
    return ''


def _extract_anthropic_text(data: dict[str, Any]) -> str:
    for block in data.get('content', []):
        if block.get('type') == 'text':
            return block.get('text', '')
    return ''

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class AudioDispatchResult:
    ok: bool
    sink: str
    detail: str
    status_code: int | None = None
    raw: dict[str, Any] | None = None


class CerberusAudioClient:
    """Small adapter for whatever CERBERUS endpoint exposes onboard Go2 speech/audio.

    The exact route can differ between forks, so both the base URL and path are
    configurable.
    """

    def __init__(
        self,
        *,
        base_url: str | None,
        speak_path: str,
        bearer_token: str | None = None,
        default_voice: str = 'sweetie-default',
        timeout_s: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip('/') if base_url else None
        self.speak_path = speak_path if speak_path.startswith('/') else f'/{speak_path}'
        self.bearer_token = bearer_token
        self.default_voice = default_voice
        self.timeout_s = timeout_s
        self.transport = transport

    def enabled(self) -> bool:
        return bool(self.base_url)

    def describe(self) -> dict[str, Any]:
        return {
            'enabled': self.enabled(),
            'sink': 'cerberus_go2_onboard_audio' if self.enabled() else 'disabled',
            'path': self.speak_path,
            'voice': self.default_voice,
        }

    def speak(
        self,
        *,
        text: str,
        voice: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AudioDispatchResult:
        if not self.enabled():
            return AudioDispatchResult(
                ok=False,
                sink='disabled',
                detail='CERBERUS audio adapter not configured',
            )
        headers = {'Content-Type': 'application/json'}
        if self.bearer_token:
            headers['Authorization'] = f'Bearer {self.bearer_token}'
        payload = {
            'text': text,
            'voice': voice or self.default_voice,
            'metadata': metadata or {},
        }
        with httpx.Client(timeout=self.timeout_s, transport=self.transport) as client:
            response = client.post(
                f'{self.base_url}{self.speak_path}',
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json() if response.content else {'status': 'ok'}
        return AudioDispatchResult(
            ok=True,
            sink='cerberus_go2_onboard_audio',
            detail='speech dispatched',
            status_code=response.status_code,
            raw=data,
        )

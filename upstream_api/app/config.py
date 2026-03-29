from __future__ import annotations

import os
from dataclasses import dataclass

PROJECT_NAME = "sweetiebot-fork"
VERSION = "0.0.7"


@dataclass(frozen=True)
class Settings:
    api_host: str = os.getenv("SWEETIEBOT_API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("SWEETIEBOT_API_PORT", "8080"))
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("SWEETIEBOT_CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ) or ("*",)
    llm_provider: str = os.getenv("SWEETIEBOT_LLM_PROVIDER", "local")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.4")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    anthropic_base_url: str = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    cerberus_audio_base_url: str | None = os.getenv("CERBERUS_AUDIO_BASE_URL")
    cerberus_audio_path: str = os.getenv("CERBERUS_AUDIO_PATH", "/audio/speak")
    cerberus_audio_token: str | None = os.getenv("CERBERUS_AUDIO_TOKEN")
    cerberus_audio_voice: str = os.getenv("CERBERUS_AUDIO_VOICE", "sweetie-default")
    request_timeout_s: float = float(os.getenv("SWEETIEBOT_REQUEST_TIMEOUT_S", "20"))


settings = Settings()

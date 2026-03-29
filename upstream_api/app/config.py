import os
from dataclasses import dataclass

PROJECT_NAME = "sweetiebot-fork"
VERSION = "0.0.4"


@dataclass(frozen=True)
class Settings:
    api_host: str = os.getenv("SWEETIEBOT_API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("SWEETIEBOT_API_PORT", "8080"))
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("SWEETIEBOT_CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ) or ("*",)


settings = Settings()

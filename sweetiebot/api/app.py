from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import FastAPI
from pydantic import BaseModel


class SpeakRequest(BaseModel):
    text: str
    voice: Optional[str] = None


def create_app(runtime_factory: Callable[[], Any]) -> FastAPI:
    app = FastAPI(title="Sweetie Bot API", version="0.1.2")

    @app.get("/character/plugins")
    def get_plugin_summary() -> Any:
        runtime = runtime_factory()
        return runtime.plugin_summary()

    @app.get("/character/health")
    def get_health() -> Any:
        runtime = runtime_factory()
        return runtime.health()

    @app.post("/character/speak-test")
    def speak_test(request: SpeakRequest) -> Any:
        runtime = runtime_factory()
        return runtime.speak(text=request.text, voice=request.voice)

    return app

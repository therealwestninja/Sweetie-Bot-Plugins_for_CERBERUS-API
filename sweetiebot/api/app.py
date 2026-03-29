from __future__ import annotations

from fastapi import FastAPI

from sweetiebot.api.routes.character import router as character_router


def create_app() -> FastAPI:
    app = FastAPI(title="Sweetie Bot API", version="0.1.0")
    app.include_router(character_router, prefix="/character", tags=["character"])
    return app


app = create_app()

from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie TTS Router",
    version=settings.plugin_version,
    description="Voice routing, style shaping, and speech synthesis request normalization.",
)

app.include_router(router)

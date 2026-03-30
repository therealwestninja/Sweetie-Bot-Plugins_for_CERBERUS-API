from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie STT Router",
    version=settings.plugin_version,
    description="Speech-to-text request normalization, transcript routing, and intent-friendly speech input layer.",
)

app.include_router(router)

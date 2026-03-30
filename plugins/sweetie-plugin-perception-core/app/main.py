from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Perception Core",
    version=settings.plugin_version,
    description="Detection ingestion, tracking, and event emission."
)
app.include_router(router)

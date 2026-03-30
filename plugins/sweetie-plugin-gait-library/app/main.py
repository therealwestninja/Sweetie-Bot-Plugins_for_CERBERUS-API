from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Gait Library Plugin",
    version=settings.plugin_version,
    description="Reusable gait-profile and movement-style adapter for CERBERUS-compatible quadruped control.",
)

app.include_router(router)

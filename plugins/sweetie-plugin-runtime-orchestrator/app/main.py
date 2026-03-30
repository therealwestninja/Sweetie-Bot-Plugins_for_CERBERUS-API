from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Runtime Orchestrator Plugin",
    version=settings.plugin_version,
    description="Cross-plugin orchestration layer for CERBERUS-compatible Sweetie plugins.",
)

app.include_router(router)

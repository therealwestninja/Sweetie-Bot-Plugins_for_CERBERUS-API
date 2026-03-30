from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Event Bus Plugin",
    version=settings.plugin_version,
    description="Typed event publish/subscribe spine for CERBERUS-compatible Sweetie plugins.",
)

app.include_router(router)

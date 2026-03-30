from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Safety Governor",
    version=settings.plugin_version,
    description="Safety policy, action constraint, and approval layer for CERBERUS-compatible Sweetie systems.",
)

app.include_router(router)

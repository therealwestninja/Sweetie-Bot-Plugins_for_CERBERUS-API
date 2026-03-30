from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Action Registry Plugin",
    version=settings.plugin_version,
    description="Named action registration, dispatch, adapter routing, and execution policy layer.",
)

app.include_router(router)

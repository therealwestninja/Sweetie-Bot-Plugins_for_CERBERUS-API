from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Behavior Engine",
    version=settings.plugin_version,
    description="Personality-driven behavior shaping, tone selection, and action styling.",
)

app.include_router(router)

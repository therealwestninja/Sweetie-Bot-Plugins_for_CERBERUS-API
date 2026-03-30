from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Cognitive Core",
    version=settings.plugin_version,
    description="Event interpretation, attention scoring, goal selection, and action suggestion layer.",
)

app.include_router(router)

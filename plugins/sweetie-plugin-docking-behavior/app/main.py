from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Docking Behavior",
    version=settings.plugin_version,
    description="Dock-seeking, approach, alignment, and charging behavior layer.",
)

app.include_router(router)

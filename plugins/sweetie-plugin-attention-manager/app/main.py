from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Attention Manager",
    version=settings.plugin_version,
    description="Multi-target attention scoring, focus selection, and priority management.",
)

app.include_router(router)

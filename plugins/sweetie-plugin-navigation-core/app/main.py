from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Navigation Core",
    version=settings.plugin_version,
    description="Goal-directed navigation planning and route generation.",
)

app.include_router(router)

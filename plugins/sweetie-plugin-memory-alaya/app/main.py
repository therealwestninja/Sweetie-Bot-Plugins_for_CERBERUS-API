from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(
    title="Sweetie Memory Alaya Plugin",
    version=settings.plugin_version,
    description="Episodic and semantic memory plugin with salience, decay, consolidation, and hybrid retrieval.",
)

app.include_router(router)

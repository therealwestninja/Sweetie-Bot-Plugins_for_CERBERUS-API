from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from upstream_api.app.config import PROJECT_NAME, VERSION, settings
from upstream_api.app.main_support import get_runtime
from upstream_api.app.routes import accessories, attention, character, events, memory, routines

app = FastAPI(title=PROJECT_NAME, version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(character.router)
app.include_router(attention.router)
app.include_router(routines.router)
app.include_router(memory.router)
app.include_router(accessories.router)
app.include_router(events.router)


@app.get("/")
def root() -> dict:
    runtime = get_runtime()
    return {
        "name": PROJECT_NAME,
        "version": VERSION,
        "status": "scaffold-online",
        "character": runtime.get_character(),
        "events": runtime.recent_events(),
    }


def main() -> None:
    import uvicorn

    uvicorn.run(
        "upstream_api.app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()

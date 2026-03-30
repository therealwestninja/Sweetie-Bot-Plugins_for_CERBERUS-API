from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Sweetie Interaction Core")
app.include_router(router)

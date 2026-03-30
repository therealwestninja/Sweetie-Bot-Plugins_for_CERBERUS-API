from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import ConsolidateRequest, IdRequest, QueryMemoryRequest, StoreMemoryRequest
from app.services.memory_store import store
from sweetie_plugin_sdk.manifest import load_manifest
from sweetie_plugin_sdk.models import ExecuteRequest, PluginResponse

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "plugin": settings.plugin_name, "version": settings.plugin_version}

@router.get("/manifest")
def manifest():
    return load_manifest()

@router.get("/status")
def status():
    return store.status()

@router.post("/execute")
def execute(req: ExecuteRequest):
    action = req.type.strip().lower()

    if action == "memory.store_episode":
        model = StoreMemoryRequest(**req.payload)
        result = store.store("episode", model.text, model.tags, model.source, model.salience, model.metadata, model.ttl_days)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"memory": result}).model_dump()

    if action == "memory.store_fact":
        model = StoreMemoryRequest(**req.payload)
        result = store.store("fact", model.text, model.tags, model.source, model.salience, model.metadata, model.ttl_days)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"memory": result}).model_dump()

    if action == "memory.query":
        model = QueryMemoryRequest(**req.payload)
        result = store.query(model.text, model.limit, model.tags)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"results": result}).model_dump()

    if action == "memory.consolidate":
        model = ConsolidateRequest(**req.payload)
        result = store.consolidate(model.min_tag_overlap)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"created": result}).model_dump()

    if action == "memory.get":
        model = IdRequest(**req.payload)
        result = store.get(model.id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Memory not found: {model.id}")
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"memory": result}).model_dump()

    if action == "memory.list":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"results": store.list()}).model_dump()

    if action == "memory.delete":
        model = IdRequest(**req.payload)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"deleted": store.delete(model.id), "id": model.id}).model_dump()

    if action == "memory.status":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=store.status()).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

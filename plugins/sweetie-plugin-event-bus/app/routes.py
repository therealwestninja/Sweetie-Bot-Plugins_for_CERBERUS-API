from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import PollRequest, PublishEventRequest, SubscribeRequest, UnsubscribeRequest
from app.services.bus import clear, poll, publish, recent, status, subscribe, unsubscribe
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
def status_route():
    return status()

@router.post("/execute")
def execute(req: ExecuteRequest):
    action = req.type.strip().lower()

    if action == "event.publish":
        model = PublishEventRequest(**req.payload)
        result = publish(model.topic, model.source, model.payload, model.tags)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "event.subscribe":
        model = SubscribeRequest(**req.payload)
        result = subscribe(model.subscriber_id, model.topics)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "event.unsubscribe":
        model = UnsubscribeRequest(**req.payload)
        result = unsubscribe(model.subscriber_id)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "event.poll":
        model = PollRequest(**req.payload)
        result = poll(model.subscriber_id, model.limit)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "event.recent":
        limit = int(req.payload.get("limit", 25))
        result = {"events": recent(limit)}
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "event.clear":
        result = clear()
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "event.status":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=status()).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

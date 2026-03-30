from fastapi import APIRouter, HTTPException
from app.config import settings
from app.models import IngestRequest, IdRequest
from app.services.tracker import ingest, list_tracks, get_track, reset
from sweetie_plugin_sdk.models import ExecuteRequest, PluginResponse
from sweetie_plugin_sdk.manifest import load_manifest

router = APIRouter()

@router.get("/health")
def health():
    return {"status":"ok","plugin":settings.plugin_name,"version":settings.plugin_version}

@router.get("/manifest")
def manifest():
    return load_manifest()

@router.post("/execute")
def execute(req: ExecuteRequest):
    action = req.type.lower()

    if action == "perception.ingest":
        model = IngestRequest(**req.payload)
        tracks, events = ingest(model.detections, model.source, model.scene)
        return PluginResponse(plugin=settings.plugin_name, action=req.type,
                              data={"tracks":tracks,"events":events}).model_dump()

    if action == "perception.track_list":
        return PluginResponse(plugin=settings.plugin_name, action=req.type,
                              data={"tracks":list_tracks()}).model_dump()

    if action == "perception.track_get":
        model = IdRequest(**req.payload)
        t = get_track(model.track_id)
        if not t:
            raise HTTPException(status_code=404, detail="track not found")
        return PluginResponse(plugin=settings.plugin_name, action=req.type,
                              data={"track":t}).model_dump()

    if action == "perception.reset":
        return PluginResponse(plugin=settings.plugin_name, action=req.type,
                              data=reset()).model_dump()

    if action == "perception.status":
        return PluginResponse(plugin=settings.plugin_name, action=req.type,
                              data={"track_count":len(list_tracks())}).model_dump()

    raise HTTPException(status_code=400, detail="unsupported action")

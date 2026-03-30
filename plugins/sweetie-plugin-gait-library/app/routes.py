from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import AdaptCommandRequest, GaitRequest, GetGaitRequest, PreviewSequenceRequest, ProfileRequest
from app.services.library import adapt_command, get_active, get_gait, list_gaits, list_profiles, preview_sequence, set_active, state
from sweetie_plugin_sdk.manifest import load_manifest
from sweetie_plugin_sdk.models import ExecuteRequest, PluginResponse

router = APIRouter()

@router.get("/health")
def health():
    return {
        "status": "ok",
        "plugin": settings.plugin_name,
        "version": settings.plugin_version,
    }

@router.get("/manifest")
def manifest():
    return load_manifest()

@router.get("/status")
def status():
    return {
        "active_profile": state.active_profile,
        "active_gait": state.active_gait,
    }

@router.post("/execute")
def execute(req: ExecuteRequest):
    action = req.type.strip().lower()
    try:
        if action == "gait.list_profiles":
            return PluginResponse(
                plugin=settings.plugin_name,
                action=req.type,
                data={"profiles": list_profiles()},
            ).model_dump()

        if action == "gait.list_gaits":
            model = ProfileRequest(**req.payload)
            return PluginResponse(
                plugin=settings.plugin_name,
                action=req.type,
                data={"profile": model.profile, "gaits": list_gaits(model.profile)},
            ).model_dump()

        if action == "gait.get_gait":
            model = GetGaitRequest(**req.payload)
            profile = model.profile or state.active_profile
            gait = get_gait(profile, model.gait)
            if not gait:
                raise HTTPException(status_code=404, detail=f"Gait not found: {profile}.{model.gait}")
            return PluginResponse(
                plugin=settings.plugin_name,
                action=req.type,
                data={"profile": profile, "gait_name": model.gait, "gait": gait},
            ).model_dump()

        if action == "gait.set_active":
            model = GaitRequest(**req.payload)
            result = set_active(model.profile, model.gait)
            return PluginResponse(
                plugin=settings.plugin_name,
                action=req.type,
                data=result,
            ).model_dump()

        if action == "gait.get_active":
            return PluginResponse(
                plugin=settings.plugin_name,
                action=req.type,
                data=get_active(),
            ).model_dump()

        if action == "gait.adapt_command":
            model = AdaptCommandRequest(**req.payload)
            return PluginResponse(
                plugin=settings.plugin_name,
                action=req.type,
                data=adapt_command(model.command, model.profile, model.gait),
            ).model_dump()

        if action == "gait.preview_sequence":
            model = PreviewSequenceRequest(**req.payload)
            return PluginResponse(
                plugin=settings.plugin_name,
                action=req.type,
                data=preview_sequence(model.profile, model.gait, model.seconds),
            ).model_dump()

        if action == "gait.status":
            return PluginResponse(
                plugin=settings.plugin_name,
                action=req.type,
                data=get_active(),
            ).model_dump()

        raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))

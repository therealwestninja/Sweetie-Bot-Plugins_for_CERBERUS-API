from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import GenerateStyleRequest, ProcessIntentRequest, SetPersonaStateRequest
from app.services.behavior import generate_style, get_persona_state, process_intent, reset_state, set_persona_state
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
    return get_persona_state()

@router.post("/execute")
def execute(req: ExecuteRequest):
    action = req.type.strip().lower()

    if action == "behavior.process_intent":
        model = ProcessIntentRequest(**req.payload)
        result = process_intent(model.intent, model.context)
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data=result,
        ).model_dump()

    if action == "behavior.generate_style":
        model = GenerateStyleRequest(**req.payload)
        result = generate_style(model.action_name, model.context)
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data=result,
        ).model_dump()

    if action == "behavior.set_persona_state":
        model = SetPersonaStateRequest(**req.payload)
        result = set_persona_state(model.model_dump())
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"state": result},
        ).model_dump()

    if action == "behavior.get_persona_state":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"state": get_persona_state()},
        ).model_dump()

    if action == "behavior.reset":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"state": reset_state()},
        ).model_dump()

    if action == "behavior.status":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data=get_persona_state(),
        ).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

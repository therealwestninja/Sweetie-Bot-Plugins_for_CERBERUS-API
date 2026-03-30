from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import EvaluateActionRequest, ReportContextRequest, SetPolicyRequest
from app.services.safety import clear_estop, estop, evaluate_action, get_policy, report_context, set_policy, status
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
def status_route():
    return status()

@router.post("/execute")
def execute(req: ExecuteRequest):
    action = req.type.strip().lower()

    if action == "safety.evaluate_action":
        model = EvaluateActionRequest(**req.payload)
        result = evaluate_action(model.action, model.context)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "safety.set_policy":
        model = SetPolicyRequest(**req.payload)
        result = set_policy(model.model_dump())
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"policy": result}).model_dump()

    if action == "safety.get_policy":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"policy": get_policy()}).model_dump()

    if action == "safety.report_context":
        model = ReportContextRequest(**req.payload)
        result = report_context(model.context)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "safety.estop":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=estop()).model_dump()

    if action == "safety.clear_estop":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=clear_estop()).model_dump()

    if action == "safety.status":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=status()).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import ActionNameRequest, ActionRegistration, DispatchRequest, SetPolicyRequest
from app.services.registry import dispatch, get_action, list_actions, register_action, set_policy, status, unregister_action
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

    if action == "action.register":
        model = ActionRegistration(**req.payload)
        result = register_action(model)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"registered": result}).model_dump()

    if action == "action.unregister":
        model = ActionNameRequest(**req.payload)
        result = unregister_action(model.action_name)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "action.list":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"results": list_actions()}).model_dump()

    if action == "action.get":
        model = ActionNameRequest(**req.payload)
        result = get_action(model.action_name)
        if not result:
            raise HTTPException(status_code=404, detail=f"Action not found: {model.action_name}")
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"result": result}).model_dump()

    if action == "action.dispatch":
        model = DispatchRequest(**req.payload)
        result = dispatch(model.action_name, model.payload_override)
        if not result:
            raise HTTPException(status_code=404, detail=f"Action not found: {model.action_name}")
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "action.set_policy":
        model = SetPolicyRequest(**req.payload)
        result = set_policy(model.action_name, model.policy)
        if not result:
            raise HTTPException(status_code=404, detail=f"Action not found: {model.action_name}")
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"updated": result}).model_dump()

    if action == "action.status":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=status()).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

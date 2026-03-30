from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import AlignRequest, BeginChargeRequest, PlanApproachRequest, SeekDockRequest, SetDockRequest
from app.services.docking import align, begin_charge, get_state, plan_approach, reset_state, seek_dock, set_dock
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
    return get_state()

@router.post("/execute")
def execute(req: ExecuteRequest):
    action = req.type.strip().lower()

    if action == "docking.set_dock":
        model = SetDockRequest(**req.payload)
        result = set_dock(model.dock_name, model.position.model_dump())
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "docking.seek_dock":
        model = SeekDockRequest(**req.payload)
        result = seek_dock(model.battery, model.current_position.model_dump())
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "docking.plan_approach":
        model = PlanApproachRequest(**req.payload)
        dock_position = model.dock_position.model_dump() if model.dock_position else None
        result = plan_approach(model.current_position.model_dump(), dock_position)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "docking.align":
        model = AlignRequest(**req.payload)
        dock_position = model.dock_position.model_dump() if model.dock_position else None
        result = align(model.current_position.model_dump(), dock_position)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "docking.begin_charge":
        model = BeginChargeRequest(**req.payload)
        result = begin_charge(model.confirmed_docked)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "docking.get_state":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=get_state()).model_dump()

    if action == "docking.reset":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=reset_state()).model_dump()

    if action == "docking.status":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=get_state()).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

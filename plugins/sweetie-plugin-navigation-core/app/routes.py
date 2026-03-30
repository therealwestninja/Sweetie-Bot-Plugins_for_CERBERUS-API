from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import FollowRouteRequest, PlanToLocationRequest, PlanToPointRequest, SetPositionRequest
from app.services.navigation import cancel_route, follow_route, get_route, plan_to_location, plan_to_point, set_position, status
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

    if action == "navigation.set_position":
        model = SetPositionRequest(**req.payload)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=set_position(model.position.model_dump())).model_dump()

    if action == "navigation.plan_to_point":
        model = PlanToPointRequest(**req.payload)
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"route": plan_to_point(model.goal.model_dump())}).model_dump()

    if action == "navigation.plan_to_location":
        model = PlanToLocationRequest(**req.payload)
        route = plan_to_location(model.name, model.locations)
        if not route:
            raise HTTPException(status_code=404, detail=f"Location not found: {model.name}")
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"route": route}).model_dump()

    if action == "navigation.follow_route":
        model = FollowRouteRequest(**req.payload)
        route = follow_route(model.route_id)
        if not route:
            raise HTTPException(status_code=404, detail=f"Route not found: {model.route_id}")
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"route": route}).model_dump()

    if action == "navigation.cancel_route":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=cancel_route()).model_dump()

    if action == "navigation.get_route":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data={"route": get_route()}).model_dump()

    if action == "navigation.status":
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=status()).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

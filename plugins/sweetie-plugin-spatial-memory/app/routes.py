from fastapi import APIRouter
from sweetie_plugin_sdk.models import ExecuteRequest, PluginResponse
from app.core import remember, get_location, list_locations, update_position, get_nearby
from app.state import state

router = APIRouter()

@router.get("/health")
def health():
    return {"status":"ok"}

@router.post("/execute")
def execute(req: ExecuteRequest):
    t = req.type
    p = req.payload

    if t == "spatial.remember_location":
        return PluginResponse(plugin="spatial", action=t, data=remember(p["name"], p["position"])).model_dump()

    if t == "spatial.get_location":
        return PluginResponse(plugin="spatial", action=t, data={"location":get_location(p["name"])}).model_dump()

    if t == "spatial.list_locations":
        return PluginResponse(plugin="spatial", action=t, data={"locations":list_locations()}).model_dump()

    if t == "spatial.update_position":
        return PluginResponse(plugin="spatial", action=t, data=update_position(p["position"])).model_dump()

    if t == "spatial.get_nearby":
        return PluginResponse(plugin="spatial", action=t, data={"nearby":get_nearby(p.get("radius",2.0))}).model_dump()

    if t == "spatial.reset":
        state.locations.clear()
        return PluginResponse(plugin="spatial", action=t, data={"reset":True}).model_dump()

    if t == "spatial.status":
        return PluginResponse(plugin="spatial", action=t, data={"state":state.__dict__}).model_dump()

    return PluginResponse(plugin="spatial", action=t, data={"info":"noop"}).model_dump()

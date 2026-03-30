from fastapi import APIRouter
from sweetie_plugin_sdk.models import ExecuteRequest, PluginResponse
from app.core import decide
from app.state import state

router = APIRouter()

@router.get("/health")
def health():
    return {"status":"ok"}

@router.post("/execute")
def execute(req: ExecuteRequest):
    t = req.type

    if t == "interaction.process_event":
        result = decide(req.payload.get("event",{}))
        return PluginResponse(plugin="interaction-core", action=t, data=result).model_dump()

    if t == "interaction.get_state":
        return PluginResponse(plugin="interaction-core", action=t, data=state.__dict__).model_dump()

    if t == "interaction.reset":
        state.engagement_target=None
        state.last_action=None
        return PluginResponse(plugin="interaction-core", action=t, data={"reset":True}).model_dump()

    return PluginResponse(plugin="interaction-core", action=t, data={"info":"noop"}).model_dump()

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import ChooseActionRequest, EvaluateContextRequest, PerceiveEventRequest, SetStateRequest
from app.services.cognition import choose_action_from_context, dump_state, evaluate_context, interpret_event, reset_state, set_state_fields
from app.services.http_clients import call_execute
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
    return dump_state()

@router.post("/execute")
async def execute(req: ExecuteRequest):
    action = req.type.strip().lower()

    if action == "cognition.perceive_event":
        model = PerceiveEventRequest(**req.payload)
        interpretation = interpret_event(model.event.model_dump())

        memory_result = None
        if interpretation["attention_score"] >= 0.6:
            memory_result = await call_execute(settings.memory_url, {
                "type": "memory.store_episode",
                "payload": {
                    "text": f"Observed event {interpretation['topic']} with intent {interpretation['intent']}.",
                    "tags": interpretation.get("tags", []),
                    "source": settings.plugin_name,
                    "salience": interpretation["attention_score"],
                    "metadata": {"event": model.event.model_dump()},
                },
            })

        bus_result = await call_execute(settings.event_bus_url, {
            "type": "event.publish",
            "payload": {
                "topic": "cognition.event_interpreted",
                "source": settings.plugin_name,
                "payload": interpretation,
                "tags": interpretation.get("tags", []),
            },
        })

        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={
                "interpretation": interpretation,
                "memory_result": memory_result,
                "bus_result": bus_result,
                "state": dump_state(),
            },
        ).model_dump()

    if action == "cognition.evaluate_context":
        model = EvaluateContextRequest(**req.payload)
        result = evaluate_context(model.context)
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"evaluation": result},
        ).model_dump()

    if action == "cognition.choose_action":
        model = ChooseActionRequest(**req.payload)
        result = choose_action_from_context(model.context)
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"suggested_action": result, "state": dump_state()},
        ).model_dump()

    if action == "cognition.set_state":
        model = SetStateRequest(**req.payload)
        result = set_state_fields(model.model_dump())
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"state": result},
        ).model_dump()

    if action == "cognition.get_state":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"state": dump_state()},
        ).model_dump()

    if action == "cognition.reset":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"state": reset_state()},
        ).model_dump()

    if action == "cognition.status":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data=dump_state(),
        ).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

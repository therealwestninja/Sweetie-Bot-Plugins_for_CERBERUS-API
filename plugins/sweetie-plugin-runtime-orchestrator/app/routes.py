from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import ChainExecuteRequest, FollowObjectRequest, PatrolMissionRequest, RegisterRoutesRequest, SimulateChainRequest
from app.services.orchestrator import build_follow_object_goal, build_patrol_mission, call_execute, register_routes, remember, state
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
        "routes": state.routes,
        "last_results": state.last_results,
    }

@router.post("/execute")
async def execute(req: ExecuteRequest):
    action = req.type.strip().lower()

    if action == "runtime.register_routes":
        model = RegisterRoutesRequest(**req.payload)
        result = register_routes(model)
        remember({"action": req.type, "result": result})
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "runtime.follow_object":
        model = FollowObjectRequest(**req.payload)
        world_resp = await call_execute(state.routes["world_model"], {
            "type": "world.get_object",
            "payload": {"id": model.object_id},
        })
        obj = world_resp["data"]["result"]
        nav_request = build_follow_object_goal(obj, model.standoff_m)
        result = {
            "world_object": obj,
            "nav_request": nav_request,
        }
        remember({"action": req.type, "result": result})
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "runtime.patrol_mission":
        model = PatrolMissionRequest(**req.payload)
        if not model.waypoints:
            raise HTTPException(status_code=400, detail="waypoints cannot be empty")
        mission = build_patrol_mission(model)
        result = {"mission_payload": mission}
        remember({"action": req.type, "result": result})
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "runtime.chain_execute":
        model = ChainExecuteRequest(**req.payload)
        if model.chain_name == "follow_operator":
            nested = await execute(ExecuteRequest(type="runtime.follow_object", payload=model.payload))
            return nested
        if model.chain_name == "patrol_basic":
            nested = await execute(ExecuteRequest(type="runtime.patrol_mission", payload=model.payload))
            return nested
        raise HTTPException(status_code=400, detail=f"Unknown chain_name: {model.chain_name}")

    if action == "runtime.simulate_chain":
        model = SimulateChainRequest(**req.payload)
        start = await call_execute(state.routes["sim"], {
            "type": "sim.episode_start",
            "payload": {
                "episode_name": model.episode_name,
                "scenario": model.scenario,
                "metadata": {"source": "runtime-orchestrator"},
            },
        })
        episode_id = start["data"]["episode"]["episode_id"]

        recorded_steps = []
        for step in model.steps:
            result = await call_execute(state.routes["sim"], {
                "type": "sim.step",
                "payload": {
                    "episode_id": episode_id,
                    "observation": step.observation,
                    "action": step.action,
                    "reward": step.reward,
                    "done": step.done,
                    "notes": step.notes,
                },
            })
            recorded_steps.append(result["data"]["step"])

        end = await call_execute(state.routes["sim"], {
            "type": "sim.episode_end",
            "payload": {
                "episode_id": episode_id,
                "outcome": "completed",
                "summary": {"step_count": len(recorded_steps)},
            },
        })

        replay = await call_execute(state.routes["sim"], {
            "type": "sim.replay_create",
            "payload": {"episode_id": episode_id},
        })

        result = {
            "episode": end["data"]["episode"],
            "replay": replay["data"]["replay"],
        }
        remember({"action": req.type, "result": {"episode_id": episode_id, "step_count": len(recorded_steps)}})
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    if action == "runtime.status":
        result = {
            "routes": state.routes,
            "last_results": state.last_results,
        }
        return PluginResponse(plugin=settings.plugin_name, action=req.type, data=result).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

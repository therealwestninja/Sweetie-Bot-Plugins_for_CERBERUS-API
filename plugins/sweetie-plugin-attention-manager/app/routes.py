from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import IngestCandidatesRequest, SetBiasRequest
from app.services.attention import get_focus, get_status, ingest_candidates, rank_candidates, reset, select_focus, set_bias
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
    return get_status()

@router.post("/execute")
def execute(req: ExecuteRequest):
    action = req.type.strip().lower()

    if action == "attention.ingest_candidates":
        model = IngestCandidatesRequest(**req.payload)
        result = ingest_candidates([c.model_dump() for c in model.candidates])
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"ranked_candidates": result},
        ).model_dump()

    if action == "attention.rank":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"ranked_candidates": rank_candidates()},
        ).model_dump()

    if action == "attention.select_focus":
        result = select_focus()
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"focus": result},
        ).model_dump()

    if action == "attention.set_bias":
        model = SetBiasRequest(**req.payload)
        result = set_bias(model.model_dump())
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"state": result},
        ).model_dump()

    if action == "attention.get_focus":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"focus": get_focus()},
        ).model_dump()

    if action == "attention.reset":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data=reset(),
        ).model_dump()

    if action == "attention.status":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data=get_status(),
        ).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

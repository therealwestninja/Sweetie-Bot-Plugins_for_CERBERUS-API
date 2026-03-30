from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import ProcessUtteranceRequest, SetDefaultsRequest, TranscribeRequest
from app.services.stt import get_defaults, list_providers, process_utterance, set_defaults, status, transcribe
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

    if action == "stt.transcribe":
        model = TranscribeRequest(**req.payload)
        result = transcribe(model.transcript, model.audio_reference, model.provider, model.language, model.metadata)
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"transcription": result},
        ).model_dump()

    if action == "stt.process_utterance":
        model = ProcessUtteranceRequest(**req.payload)
        result = process_utterance(model.transcript, model.speaker_id, model.provider, model.language, model.metadata)
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"utterance": result},
        ).model_dump()

    if action == "stt.list_providers":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"providers": list_providers()},
        ).model_dump()

    if action == "stt.set_defaults":
        model = SetDefaultsRequest(**req.payload)
        result = set_defaults(model.model_dump())
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"defaults": result},
        ).model_dump()

    if action == "stt.get_defaults":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"defaults": get_defaults()},
        ).model_dump()

    if action == "stt.status":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data=status(),
        ).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

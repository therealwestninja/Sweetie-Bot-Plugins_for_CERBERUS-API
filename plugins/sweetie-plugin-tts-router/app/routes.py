from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import PreviewVoiceRequest, SetDefaultsRequest, SpeakRequest
from app.services.tts import build_speech, get_defaults, list_voices, preview_voice, set_defaults, status
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

    if action == "tts.speak":
        model = SpeakRequest(**req.payload)
        result = build_speech(model.text, model.tone, model.emotion, model.voice, model.provider, model.rate, model.pitch, model.metadata)
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"speech_envelope": result},
        ).model_dump()

    if action == "tts.preview_voice":
        model = PreviewVoiceRequest(**req.payload)
        result = preview_voice(model.voice, model.sample_text)
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"speech_envelope": result},
        ).model_dump()

    if action == "tts.list_voices":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"voices": list_voices()},
        ).model_dump()

    if action == "tts.set_defaults":
        model = SetDefaultsRequest(**req.payload)
        result = set_defaults(model.model_dump())
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"defaults": result},
        ).model_dump()

    if action == "tts.get_defaults":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data={"defaults": get_defaults()},
        ).model_dump()

    if action == "tts.status":
        return PluginResponse(
            plugin=settings.plugin_name,
            action=req.type,
            data=status(),
        ).model_dump()

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.type}")

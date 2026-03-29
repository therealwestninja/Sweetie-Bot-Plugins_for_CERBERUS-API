from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from upstream_api.app.main_support import get_runtime
from upstream_api.app.services.runtime import RuntimeState

router = APIRouter(prefix="/character", tags=["character"])


class SayRequest(BaseModel):
    text: str = Field(min_length=1, max_length=400)


class EmoteRequest(BaseModel):
    emote_id: str | None = None


class RoutineRequest(BaseModel):
    routine_id: str = Field(min_length=1)


class FocusRequest(BaseModel):
    target_id: str = Field(min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    mode: str = Field(default="person")


class PersonaRequest(BaseModel):
    persona_id: str = Field(min_length=1)


@router.get("")
def get_character(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.get_character()


@router.get("/personas")
def get_personas(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return {"items": runtime.list_personas()}


@router.get("/foundation")
def get_foundation(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.get_persona_foundation()


@router.post("/persona")
def set_persona(payload: PersonaRequest, runtime: RuntimeState = Depends(get_runtime)) -> dict:
    try:
        return runtime.apply_persona(payload.persona_id)
    except KeyError as exc:
        detail = f"Unknown persona: {payload.persona_id}"
        raise HTTPException(status_code=404, detail=detail) from exc


@router.get("/llm")
def get_llm_status(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.get_llm_status()


@router.post("/say")
def say(payload: SayRequest, runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.say(payload.text)


@router.post("/emote")
def emote(payload: EmoteRequest, runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.emote(payload.emote_id)


@router.post("/routine")
def routine(payload: RoutineRequest, runtime: RuntimeState = Depends(get_runtime)) -> dict:
    try:
        return runtime.run_routine(payload.routine_id)
    except KeyError as exc:
        detail = f"Unknown routine: {payload.routine_id}"
        raise HTTPException(status_code=404, detail=detail) from exc


@router.post("/focus")
def focus(payload: FocusRequest, runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.focus(payload.target_id, payload.confidence, payload.mode)


@router.post("/cancel")
def cancel(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.cancel()

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from sweetiebot.runtime import SweetieBotRuntime

router = APIRouter()
runtime = SweetieBotRuntime()


class SayRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class PersonaRequest(BaseModel):
    payload: dict[str, Any]


class PluginConfigRequest(BaseModel):
    plugins: dict[str, dict[str, Any]]


@router.get("/foundation")
def foundation() -> dict[str, Any]:
    rules = runtime.dialogue.rules
    return {
        "persona_id": runtime.state.persona_id,
        "dialogue_style": rules.dialogue_style,
        "defaults": {
            "emote": rules.default_emote,
            "routine": rules.default_routine,
            "accessory_scene": rules.default_accessory_scene,
        },
        "limits": rules.limits,
        "state": runtime.state.to_dict(),
    }


@router.get("/state")
def state() -> dict[str, Any]:
    return runtime.state.to_dict()


@router.get("/plugins")
def plugins() -> dict[str, Any]:
    return {"plugins": runtime.plugin_summary()}


@router.post("/plugins/configure")
def configure_plugins(request: PluginConfigRequest) -> dict[str, Any]:
    configured = runtime.configure_plugins(request.plugins)
    return {"ok": True, "configured": configured, "plugins": runtime.plugin_summary()}


@router.post("/persona")
def set_persona(request: PersonaRequest) -> dict[str, Any]:
    state = runtime.configure_persona(request.payload)
    return {"ok": True, "state": state.to_dict()}


@router.post("/say")
def say(request: SayRequest) -> dict[str, Any]:
    return runtime.handle_text(request.text)


@router.post("/stop")
def stop() -> dict[str, Any]:
    state = runtime.apply_operator_stop()
    return {"ok": True, "state": state.to_dict()}


@router.post("/reset-neutral")
def reset_neutral() -> dict[str, Any]:
    state = runtime.reset_neutral()
    return {"ok": True, "state": state.to_dict()}

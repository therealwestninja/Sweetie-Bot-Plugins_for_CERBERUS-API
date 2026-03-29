from fastapi import APIRouter, Depends
from pydantic import BaseModel

from upstream_api.app.main_support import get_runtime
from upstream_api.app.services.runtime import RuntimeState

router = APIRouter(prefix="/accessories", tags=["accessories"])


class AccessorySceneRequest(BaseModel):
    scene_id: str | None = None


@router.get("")
def get_accessories(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.get_accessories()


@router.get("/scenes")
def get_accessory_scenes(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return {"items": runtime.get_accessories()["catalog"]}


@router.post("/scene")
def apply_accessory_scene(
    payload: AccessorySceneRequest, runtime: RuntimeState = Depends(get_runtime)
) -> dict:
    return runtime.apply_accessory_scene(payload.scene_id)

from fastapi import APIRouter, Depends

from upstream_api.app.main_support import get_runtime
from upstream_api.app.services.runtime import RuntimeState

router = APIRouter(prefix="/emotes", tags=["emotes"])


@router.get("")
def get_emotes(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.get_emotes()

from fastapi import APIRouter, Depends

from upstream_api.app.main_support import get_runtime
from upstream_api.app.services.runtime import RuntimeState

router = APIRouter(prefix="/routines", tags=["routines"])


@router.get("")
def get_routines(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.get_routines()

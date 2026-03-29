from fastapi import APIRouter, Depends, HTTPException

from upstream_api.app.main_support import get_runtime
from upstream_api.app.services.runtime import RuntimeState

router = APIRouter(prefix="/routines", tags=["routines"])


@router.get("")
def get_routines(runtime: RuntimeState = Depends(get_runtime)) -> dict:
    return runtime.get_routines()


@router.get("/{routine_id}/plan")
def get_routine_plan(routine_id: str, runtime: RuntimeState = Depends(get_runtime)) -> dict:
    try:
        return runtime.get_routine_plan(routine_id)
    except KeyError as exc:
        detail = f"Unknown routine: {routine_id}"
        raise HTTPException(status_code=404, detail=detail) from exc

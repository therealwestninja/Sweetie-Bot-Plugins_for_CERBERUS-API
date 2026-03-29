
from typing import Optional


class RoutineExecutor:
    def __init__(self, adapter):
        self.adapter = adapter
        self.active_routine: Optional[str] = None

    def execute(self, routine_id: Optional[str]):
        if not routine_id:
            return {"status": "no_routine"}

        self.active_routine = routine_id
        result = self.adapter.execute_routine(routine_id)
        return {
            "active_routine": routine_id,
            "adapter_result": result
        }

    def interrupt(self):
        self.active_routine = None
        return {"status": "interrupted"}

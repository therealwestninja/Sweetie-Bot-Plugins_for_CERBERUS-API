from __future__ import annotations

from typing import Any, Dict, List

from sweetiebot.memory.models import MemoryQuery, MemoryRecord


class BasePlugin:
    plugin_id: str = "base.plugin"
    plugin_type: str = "base"

    def manifest(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_type": self.plugin_type,
            "version": "0.1.0",
            "healthy": True,
            "capabilities": [],
        }

    def configure(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def healthcheck(self) -> Dict[str, Any]:
        return {"healthy": True, "plugin_id": self.plugin_id}

    def shutdown(self) -> None:
        return None


class MemoryStorePlugin(BasePlugin):
    plugin_type = "memory_store"

    def put(self, record: MemoryRecord) -> MemoryRecord:
        raise NotImplementedError

    def query(self, query: MemoryQuery) -> List[MemoryRecord]:
        raise NotImplementedError

    def recent(self, limit: int = 10) -> List[MemoryRecord]:
        return self.query(MemoryQuery(limit=limit))

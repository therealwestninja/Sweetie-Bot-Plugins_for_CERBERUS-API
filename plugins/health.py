from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List


class PluginHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"


@dataclass(slots=True)
class PluginHealthCheck:
    plugin_id: str
    status: PluginHealthStatus = PluginHealthStatus.HEALTHY
    summary: str = "OK"
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def ok(self) -> bool:
        return self.status != PluginHealthStatus.ERROR

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["ok"] = self.ok
        return payload


@dataclass(slots=True)
class PluginHealthSnapshot:
    plugin_id: str
    plugin_type: str
    ok: bool
    status: str = "healthy"
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _normalize_health(plugin: Any) -> Dict[str, Any]:
    raw = plugin.healthcheck()
    if isinstance(raw, PluginHealthCheck):
        return raw.to_dict()
    if isinstance(raw, dict):
        if "healthy" in raw and "ok" not in raw:
            raw = dict(raw)
            raw["ok"] = bool(raw.pop("healthy"))
        raw.setdefault("ok", True)
        raw.setdefault("status", "healthy" if raw["ok"] else "error")
        raw.setdefault("details", {})
        return raw
    return {"ok": True, "status": "healthy", "details": {"raw": raw}}


def collect_plugin_health(plugins: Iterable[Any]) -> List[PluginHealthSnapshot]:
    snapshots: List[PluginHealthSnapshot] = []
    for plugin in plugins:
        manifest = plugin.manifest()
        try:
            health = _normalize_health(plugin)
        except Exception as exc:  # pragma: no cover
            health = {"ok": False, "status": "error", "details": {"error": str(exc)}}
        plugin_type = getattr(manifest.plugin_type, "value", str(manifest.plugin_type))
        snapshots.append(
            PluginHealthSnapshot(
                plugin_id=manifest.plugin_id,
                plugin_type=plugin_type,
                ok=bool(health["ok"]),
                status=str(health["status"]),
                details=dict(health.get("details") or {}),
            )
        )
    return snapshots


def summarize_plugin_health(plugins: Iterable[Any]) -> Dict[str, Any]:
    snapshots = collect_plugin_health(plugins)
    total = len(snapshots)
    healthy = sum(1 for s in snapshots if s.ok and s.status == "healthy")
    degraded = sum(1 for s in snapshots if s.status == "degraded")
    errors = sum(1 for s in snapshots if not s.ok)
    families = sorted({s.plugin_type for s in snapshots})
    return {
        "ok": errors == 0,
        "overall_status": "healthy" if errors == 0 else "error",
        "counts": {
            "total": total,
            "healthy": healthy,
            "degraded": degraded,
            "errors": errors,
        },
        "families": families,
        "plugins": [s.to_dict() for s in snapshots],
    }

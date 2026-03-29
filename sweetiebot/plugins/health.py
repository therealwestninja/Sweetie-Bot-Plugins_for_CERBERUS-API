from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class PluginHealthSnapshot:
    plugin_id: str
    plugin_type: str
    ok: bool
    status: str = "ok"
    details: Optional[Dict[str, Any]] = None
    checked_at: str = ""

    def __post_init__(self) -> None:
        if not self.checked_at:
            self.checked_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def collect_plugin_health(plugins: Iterable[Any]) -> List[PluginHealthSnapshot]:
    snapshots: List[PluginHealthSnapshot] = []
    for plugin in plugins:
        manifest = plugin.manifest()
        try:
            raw = plugin.healthcheck()
            ok = bool(raw.get("ok", True))
            status = str(raw.get("status", "ok"))
            details = raw.get("details") or {}
        except Exception as exc:  # pragma: no cover - defensive
            ok = False
            status = "error"
            details = {"error": str(exc)}
        snapshots.append(
            PluginHealthSnapshot(
                plugin_id=manifest.plugin_id,
                plugin_type=manifest.plugin_type.value if hasattr(manifest.plugin_type, "value") else str(manifest.plugin_type),
                ok=ok,
                status=status,
                details=details,
            )
        )
    return snapshots


def summarize_plugin_health(plugins: Iterable[Any]) -> Dict[str, Any]:
    snapshots = collect_plugin_health(plugins)
    total = len(snapshots)
    healthy = sum(1 for item in snapshots if item.ok)
    degraded = sum(1 for item in snapshots if item.status == "degraded")
    errors = sum(1 for item in snapshots if not item.ok)
    return {
        "ok": errors == 0,
        "counts": {
            "total": total,
            "healthy": healthy,
            "degraded": degraded,
            "errors": errors,
        },
        "plugins": [item.to_dict() for item in snapshots],
    }

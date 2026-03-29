from __future__ import annotations

import json
from pathlib import Path


class AccessoryManager:
    def __init__(self, assets_path: str | Path | None = None) -> None:
        self.state = {
            "face_display": False,
            "tail_servo": False,
            "speaker_stack": True,
        }
        self._assets: dict[str, dict] = {}
        self.active_scene: str | None = None
        self.applied_payload: dict = {}
        if assets_path is not None:
            self.load_assets(assets_path)

    def load_assets(self, assets_path: str | Path) -> None:
        path = Path(assets_path)
        if not path.exists():
            return
        for asset in sorted(path.glob("*.json")):
            with open(asset, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            asset_id = payload.get("id") or asset.stem
            payload.setdefault("id", asset_id)
            self._assets[asset_id] = payload

    def capabilities(self) -> dict:
        return {
            "state": dict(self.state),
            "catalog": self.catalog(),
            "active_scene": self.active_scene,
            "applied_payload": dict(self.applied_payload),
        }

    def catalog(self) -> list[dict]:
        return [self._assets[key] for key in sorted(self._assets)]

    def get_asset(self, asset_id: str) -> dict | None:
        return self._assets.get(asset_id)

    def apply_scene(self, scene_id: str | None, *, fallback_payload: dict | None = None) -> dict:
        payload = {}
        if scene_id:
            payload = dict(self._assets.get(scene_id, {"id": scene_id, "kind": "virtual"}))
        elif fallback_payload:
            payload = dict(fallback_payload)
            payload.setdefault("id", "inline")
        self.active_scene = payload.get("id") if payload else None
        self.applied_payload = payload
        return payload

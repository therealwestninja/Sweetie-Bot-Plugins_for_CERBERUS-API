from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EmoteCommand:
    emote_id: str
    duration_ms: int = 1500
    accessories: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


class EmoteMapper:
    def __init__(self, emotes_path: str | Path | None = None) -> None:
        self._catalog: dict[str, dict] = {}
        if emotes_path is not None:
            self.load_assets(emotes_path)

    def load_assets(self, emotes_path: str | Path) -> None:
        path = Path(emotes_path)
        if not path.exists():
            return
        for asset in sorted(path.glob("*.json")):
            with open(asset, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self._catalog[payload["id"]] = payload

    def describe_emote(self, emote_id: str) -> dict | None:
        return self._catalog.get(emote_id)

    def catalog(self) -> list[dict]:
        return [self._catalog[key] for key in sorted(self._catalog)]

    def for_mood(self, mood: str) -> EmoteCommand:
        mapping = {
            "curious": "curious_headtilt",
            "happy": "happy_bounce",
            "bashful": "bashful_shift",
            "apologetic": "bashful_shift",
            "excited": "happy_bounce",
        }
        emote_id = mapping.get(mood, "curious_headtilt")
        return self._command_for_id(emote_id)

    def _command_for_id(self, emote_id: str) -> EmoteCommand:
        payload = self._catalog.get(emote_id, {"id": emote_id, "default_duration_ms": 1500})
        return EmoteCommand(
            emote_id=payload["id"],
            duration_ms=payload.get("default_duration_ms", 1500),
            accessories=payload.get("linked_accessories", {}),
            tags=payload.get("tags", []),
        )

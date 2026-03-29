from dataclasses import dataclass


@dataclass
class SyncPlan:
    speech_key: str | None = None
    emote_id: str | None = None
    accessory_expression: str | None = None

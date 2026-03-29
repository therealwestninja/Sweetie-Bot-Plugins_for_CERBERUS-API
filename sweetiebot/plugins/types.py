from __future__ import annotations

from enum import StrEnum


class PluginType(StrEnum):
    DIALOGUE_PROVIDER = "dialogue_provider"
    ROUTINE_PACK = "routine_pack"
    SAFETY_POLICY = "safety_policy"

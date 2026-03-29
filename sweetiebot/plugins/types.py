from __future__ import annotations

from enum import Enum


class PluginType(str, Enum):
    PERSONA = "persona"
    DIALOGUE_PROVIDER = "dialogue_provider"
    EMOTE_MAPPER = "emote_mapper"
    ROUTINE_PACK = "routine_pack"
    ATTENTION_STRATEGY = "attention_strategy"
    ACCESSORY_SCENE_PROVIDER = "accessory_scene_provider"
    TTS_PROVIDER = "tts_provider"
    AUDIO_OUTPUT = "audio_output"
    CERBERUS_ADAPTER = "cerberus_adapter"
    MEMORY_STORE = "memory_store"
    PERCEPTION_SOURCE = "perception_source"
    SAFETY_POLICY = "safety_policy"
    TELEMETRY_SINK = "telemetry_sink"
    OPERATOR_CONTROL = "operator_control"
    ASSET_PACK = "asset_pack"
    # ── Integration layer (added by Sweetie-Bot CERBERUS integration) ──
    CERBERUS_MAPPER    = "cerberus_mapper"
    SAFETY_GATE        = "safety_gate"
    MEMORY_CONTEXT     = "memory_context"


PluginFamily = PluginType

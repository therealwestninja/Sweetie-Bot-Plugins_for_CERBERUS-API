from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC

from app.config import settings

VOICE_LIBRARY = {
    "sweetie_bright": {
        "label": "Sweetie Bright",
        "base_rate": 1.08,
        "base_pitch": 1.12,
        "style_tags": ["youthful", "playful", "wholesome"],
    },
    "sweetie_soft": {
        "label": "Sweetie Soft",
        "base_rate": 0.98,
        "base_pitch": 1.05,
        "style_tags": ["gentle", "kind", "soft"],
    },
    "sweetie_excited": {
        "label": "Sweetie Excited",
        "base_rate": 1.16,
        "base_pitch": 1.18,
        "style_tags": ["enthusiastic", "bubbly", "expressive"],
    },
}

@dataclass
class TTSState:
    provider: str = settings.default_provider
    voice: str = settings.default_voice
    rate: float = settings.default_rate
    pitch: float = settings.default_pitch
    recent_requests: list[dict] = field(default_factory=list)

state = TTSState()

def now_iso() -> str:
    return datetime.now(UTC).isoformat()

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))

def tone_adjustments(tone: str, emotion: str) -> tuple[float, float, list[str]]:
    rate_adj = 1.0
    pitch_adj = 1.0
    tags = []
    if tone == "bright_cheerful":
        rate_adj *= 1.04
        pitch_adj *= 1.03
        tags += ["bright", "cheerful"]
    elif tone == "soft_careful":
        rate_adj *= 0.95
        pitch_adj *= 0.98
        tags += ["soft", "careful"]
    elif tone == "dramatic_cute":
        rate_adj *= 1.02
        pitch_adj *= 1.05
        tags += ["dramatic", "cute"]
    else:
        tags += ["warm", "playful"]

    if emotion == "excited":
        rate_adj *= 1.05
        pitch_adj *= 1.04
        tags.append("excited")
    elif emotion == "nervous":
        rate_adj *= 1.01
        pitch_adj *= 1.02
        tags.append("nervous")
    elif emotion == "tired":
        rate_adj *= 0.93
        pitch_adj *= 0.97
        tags.append("tired")
    elif emotion == "happy":
        pitch_adj *= 1.02
        tags.append("happy")
    return rate_adj, pitch_adj, tags

def list_voices() -> list[dict]:
    out = []
    for name, meta in VOICE_LIBRARY.items():
        out.append({"voice": name, **meta})
    return out

def set_defaults(data: dict) -> dict:
    if data.get("provider"):
        state.provider = str(data["provider"])
    if data.get("voice"):
        state.voice = str(data["voice"])
    if data.get("rate") is not None:
        state.rate = clamp(data["rate"], 0.5, 2.0)
    if data.get("pitch") is not None:
        state.pitch = clamp(data["pitch"], 0.5, 2.0)
    return get_defaults()

def get_defaults() -> dict:
    return {
        "provider": state.provider,
        "voice": state.voice,
        "rate": state.rate,
        "pitch": state.pitch,
    }

def build_speech(text: str, tone: str, emotion: str, voice: str | None, provider: str | None, rate: float | None, pitch: float | None, metadata: dict) -> dict:
    selected_voice = voice or state.voice
    voice_meta = VOICE_LIBRARY.get(selected_voice, VOICE_LIBRARY["sweetie_bright"])
    selected_provider = provider or state.provider

    base_rate = rate if rate is not None else voice_meta["base_rate"] * state.rate
    base_pitch = pitch if pitch is not None else voice_meta["base_pitch"] * state.pitch
    rate_adj, pitch_adj, extra_tags = tone_adjustments(tone, emotion)

    envelope = {
        "provider": selected_provider,
        "voice": selected_voice,
        "text": text,
        "rate": round(clamp(base_rate * rate_adj, 0.5, 2.0), 4),
        "pitch": round(clamp(base_pitch * pitch_adj, 0.5, 2.0), 4),
        "tone": tone,
        "emotion": emotion,
        "style_tags": list(dict.fromkeys(voice_meta["style_tags"] + extra_tags)),
        "metadata": metadata,
        "synthesis_request": {
            "provider": selected_provider,
            "voice": selected_voice,
            "text": text,
        },
    }
    state.recent_requests.append({"at": now_iso(), **envelope})
    state.recent_requests = state.recent_requests[-20:]
    return envelope

def preview_voice(voice: str, sample_text: str) -> dict:
    return build_speech(sample_text, "warm_playful", "neutral", voice, None, None, None, {"preview": True})

def status() -> dict:
    return {
        **get_defaults(),
        "voices": list_voices(),
        "recent_requests": state.recent_requests[-10:],
    }

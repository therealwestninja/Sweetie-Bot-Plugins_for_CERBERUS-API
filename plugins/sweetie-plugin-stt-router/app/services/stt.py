from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC

from app.config import settings

PROVIDERS = [
    {"provider": "mock", "kind": "local_stub", "notes": "Transcript-first development mode"},
    {"provider": "whisper_local", "kind": "local", "notes": "Planned local STT backend"},
    {"provider": "cloud_openai_compatible", "kind": "remote", "notes": "Planned remote STT backend"},
]

@dataclass
class STTState:
    provider: str = settings.default_provider
    language: str = settings.default_language
    mode: str = settings.default_mode
    recent_requests: list[dict] = field(default_factory=list)

state = STTState()

def now_iso() -> str:
    return datetime.now(UTC).isoformat()

def set_defaults(data: dict) -> dict:
    if data.get("provider"):
        state.provider = str(data["provider"])
    if data.get("language"):
        state.language = str(data["language"])
    if data.get("mode"):
        state.mode = str(data["mode"])
    return get_defaults()

def get_defaults() -> dict:
    return {
        "provider": state.provider,
        "language": state.language,
        "mode": state.mode,
    }

def list_providers() -> list[dict]:
    return PROVIDERS

def transcribe(transcript: str | None, audio_reference: str | None, provider: str | None, language: str | None, metadata: dict) -> dict:
    selected_provider = provider or state.provider
    selected_language = language or state.language

    if transcript:
        text = transcript.strip()
        source_kind = "direct_transcript"
    elif audio_reference:
        text = f"[mock transcript from {audio_reference}]"
        source_kind = "mock_audio_reference"
    else:
        text = ""
        source_kind = "empty"

    result = {
        "provider": selected_provider,
        "language": selected_language,
        "source_kind": source_kind,
        "transcript": text,
        "metadata": metadata,
    }
    state.recent_requests.append({"at": now_iso(), "type": "transcribe", **result})
    state.recent_requests = state.recent_requests[-20:]
    return result

def classify_utterance(text: str) -> dict:
    normalized = text.lower().strip()

    command_patterns = [
        (["follow me", "come with me"], "follow_operator", {"target": "speaker"}, 0.91),
        (["stop", "freeze", "stay there"], "stop_motion", {}, 0.93),
        (["come here", "come to me"], "approach_speaker", {"target": "speaker"}, 0.9),
        (["go dock", "go to the dock", "go charge"], "seek_dock", {}, 0.9),
        (["look at me", "watch me"], "observe_person", {"target": "speaker"}, 0.84),
        (["what do you see", "what's over there"], "report_observation", {}, 0.72),
    ]

    for phrases, cmd, entities, conf in command_patterns:
        if any(p in normalized for p in phrases):
            return {
                "intent_type": "command",
                "command_name": cmd,
                "confidence": conf,
                "entities": entities,
            }

    if normalized.endswith("?") or normalized.startswith(("what", "why", "how", "who", "where", "can you")):
        return {
            "intent_type": "question",
            "command_name": None,
            "confidence": 0.7,
            "entities": {},
        }

    if any(w in normalized for w in ["hi", "hello", "hey sweetie", "good girl"]):
        return {
            "intent_type": "social",
            "command_name": "greet_back",
            "confidence": 0.79,
            "entities": {},
        }

    return {
        "intent_type": "chat",
        "command_name": None,
        "confidence": 0.55,
        "entities": {},
    }

def process_utterance(transcript: str, speaker_id: str | None, provider: str | None, language: str | None, metadata: dict) -> dict:
    transcribed = transcribe(transcript, None, provider, language, metadata)
    classification = classify_utterance(transcribed["transcript"])
    result = {
        **transcribed,
        "speaker_id": speaker_id,
        **classification,
    }
    state.recent_requests.append({"at": now_iso(), "type": "process_utterance", **result})
    state.recent_requests = state.recent_requests[-20:]
    return result

def status() -> dict:
    return {
        **get_defaults(),
        "providers": list_providers(),
        "recent_requests": state.recent_requests[-10:],
    }

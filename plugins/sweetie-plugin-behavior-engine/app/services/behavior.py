from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC

from app.config import settings

def now_iso() -> str:
    return datetime.now(UTC).isoformat()

def clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))

@dataclass
class PersonaState:
    energy: float = settings.default_energy
    curiosity: float = settings.default_curiosity
    affection: float = settings.default_affection
    drama: float = settings.default_drama
    caution: float = settings.default_caution
    mood: str = "bubbly"
    recent_behaviors: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

state = PersonaState()

def remember(entry: dict):
    state.recent_behaviors.append({"at": now_iso(), **entry})
    state.recent_behaviors = state.recent_behaviors[-25:]

def tone_from_state() -> str:
    if state.energy > 0.8 and state.affection > 0.7:
        return "bright_cheerful"
    if state.caution > 0.7:
        return "soft_careful"
    if state.drama > 0.7:
        return "dramatic_cute"
    return "warm_playful"

def movement_from_intent(intent: str) -> str:
    if intent in {"engage_operator", "follow_operator"}:
        return "light_trot"
    if intent in {"observe_person", "observe"}:
        return "gentle_step"
    if intent in {"explore_novel_object", "inspect"}:
        return "curious_prance"
    if intent in {"retreat", "avoid_hazard"}:
        return "careful_backstep"
    return "idle_bounce"

def attention_bias_from_intent(intent: str, context: dict) -> str:
    if context.get("is_operator"):
        return "operator_locked"
    if intent in {"explore_novel_object", "inspect"}:
        return "novelty_seek"
    if intent in {"observe_person", "engage_operator"}:
        return "social_focus"
    return "balanced"

def speech_for(intent: str, context: dict) -> str | None:
    if intent == "engage_operator":
        return "Ooo! There you are! I'll come with you!"
    if intent == "follow_operator":
        return "Okay! I'm right behind you!"
    if intent == "observe_person":
        return "Hi! I see somepony over there."
    if intent == "explore_novel_object":
        return "Oh! What's that? Can we check it out?"
    if intent == "encourage_friend":
        return "We can do it! Let's try together!"
    if intent == "avoid_hazard":
        return "Eep! Better be careful."
    if intent == "idle":
        return "Hmm... I wonder what we should do next."
    return None

def behavior_mode(intent: str, context: dict) -> str:
    if intent == "engage_operator":
        return "excited_follow"
    if intent == "follow_operator":
        return "loyal_follow"
    if intent == "observe_person":
        return "friendly_observe"
    if intent == "explore_novel_object":
        return "curious_investigate"
    if intent == "encourage_friend":
        return "supportive_cheer"
    if intent == "avoid_hazard":
        return "cautious_retreat"
    return "bubbly_idle"

def process_intent(intent: str, context: dict) -> dict:
    if context.get("battery", 1.0) < 0.2:
        state.mood = "tired_but_sweet"
    elif intent in {"engage_operator", "follow_operator"}:
        state.mood = "excited"
    elif intent in {"observe_person", "encourage_friend"}:
        state.mood = "warm"
    elif intent in {"avoid_hazard"}:
        state.mood = "nervous"
    else:
        state.mood = "curious"

    result = {
        "behavior_mode": behavior_mode(intent, context),
        "tone": tone_from_state(),
        "speech": speech_for(intent, context),
        "movement_style": movement_from_intent(intent),
        "attention_bias": attention_bias_from_intent(intent, context),
        "mood": state.mood,
        "character_envelope": {
            "style_tags": [
                "wholesome",
                "playful",
                "youthful",
                "expressive",
            ],
            "energy": round(state.energy, 3),
            "curiosity": round(state.curiosity, 3),
            "affection": round(state.affection, 3),
            "drama": round(state.drama, 3),
            "caution": round(state.caution, 3),
        },
    }
    remember({"intent": intent, "result": result})
    return result

def generate_style(action_name: str, context: dict) -> dict:
    intent_map = {
        "follow_operator": "follow_operator",
        "observe_person": "observe_person",
        "idle_scan": "idle",
        "avoid_hazard": "avoid_hazard",
        "explore_object": "explore_novel_object",
    }
    return process_intent(intent_map.get(action_name, "idle"), context)

def set_persona_state(data: dict) -> dict:
    for field in ["energy", "curiosity", "affection", "drama", "caution"]:
        if data.get(field) is not None:
            setattr(state, field, clamp01(data[field]))
    if data.get("notes"):
        state.notes.extend(data["notes"])
        state.notes = state.notes[-20:]
    return get_persona_state()

def get_persona_state() -> dict:
    return {
        "energy": state.energy,
        "curiosity": state.curiosity,
        "affection": state.affection,
        "drama": state.drama,
        "caution": state.caution,
        "mood": state.mood,
        "recent_behaviors": state.recent_behaviors[-10:],
        "notes": state.notes[-10:],
    }

def reset_state() -> dict:
    state.energy = settings.default_energy
    state.curiosity = settings.default_curiosity
    state.affection = settings.default_affection
    state.drama = settings.default_drama
    state.caution = settings.default_caution
    state.mood = "bubbly"
    state.recent_behaviors.clear()
    state.notes.clear()
    return get_persona_state()

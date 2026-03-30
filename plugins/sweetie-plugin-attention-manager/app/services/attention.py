from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict

from app.config import settings

def now_iso() -> str:
    return datetime.now(UTC).isoformat()

def clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))

@dataclass
class AttentionState:
    novelty_weight: float = settings.novelty_weight
    social_weight: float = settings.social_weight
    salience_weight: float = settings.salience_weight
    candidates: Dict[str, dict] = field(default_factory=dict)
    current_focus: dict | None = None
    focus_history: list[dict] = field(default_factory=list)

state = AttentionState()

def social_score(candidate: dict) -> float:
    tags = set(candidate.get("tags", []))
    if "operator" in tags:
        return 1.0
    if candidate.get("label") == "person":
        return 0.85
    if "pet" in tags:
        return 0.6
    return 0.2

def distance_modifier(distance_m: float) -> float:
    if distance_m <= 0:
        return 1.0
    if distance_m < 1.0:
        return 1.0
    if distance_m < 2.0:
        return 0.9
    if distance_m < 4.0:
        return 0.75
    return 0.55

def score_candidate(candidate: dict) -> float:
    novelty = clamp01(candidate.get("novelty", 0.0))
    salience = clamp01(candidate.get("salience", 0.5))
    confidence = clamp01(candidate.get("confidence", 0.5))
    persistence = clamp01(candidate.get("persistence", 0.0))
    social = social_score(candidate)
    distance = float(candidate.get("distance_m", 0.0))
    base = (
        novelty * state.novelty_weight
        + social * state.social_weight
        + salience * state.salience_weight
    )
    score = (base * confidence * distance_modifier(distance)) + (persistence * 0.15)
    return round(clamp01(score), 6)

def ingest_candidates(candidates: list[dict]) -> list[dict]:
    ranked = []
    for raw in candidates:
        target_id = raw["target_id"]
        if target_id in state.candidates:
            prev = state.candidates[target_id]
            raw["persistence"] = round(min(1.0, float(prev.get("persistence", 0.0)) + 0.2), 4)
        else:
            raw["persistence"] = round(float(raw.get("persistence", 0.0)), 4)
        raw["attention_score"] = score_candidate(raw)
        state.candidates[target_id] = raw
        ranked.append(raw)
    ranked.sort(key=lambda x: x["attention_score"], reverse=True)
    return ranked

def rank_candidates() -> list[dict]:
    ranked = []
    for target_id, cand in list(state.candidates.items()):
        cand["attention_score"] = score_candidate(cand)
        ranked.append(cand)
    ranked.sort(key=lambda x: x["attention_score"], reverse=True)
    return ranked

def select_focus() -> dict | None:
    ranked = rank_candidates()
    if not ranked:
        state.current_focus = None
        return None

    selected = ranked[0]
    prev = state.current_focus
    if prev and prev.get("target_id") != selected.get("target_id"):
        prev_score = float(prev.get("attention_score", 0.0))
        new_score = float(selected.get("attention_score", 0.0))
        if new_score < prev_score + 0.12:
            selected = prev

    state.current_focus = selected
    state.focus_history.append({
        "at": now_iso(),
        "focus": selected,
    })
    state.focus_history = state.focus_history[-25:]
    return selected

def set_bias(data: dict) -> dict:
    if data.get("novelty_weight") is not None:
        state.novelty_weight = clamp01(data["novelty_weight"])
    if data.get("social_weight") is not None:
        state.social_weight = clamp01(data["social_weight"])
    if data.get("salience_weight") is not None:
        state.salience_weight = clamp01(data["salience_weight"])
    return get_status()

def get_focus() -> dict | None:
    return state.current_focus

def reset() -> dict:
    state.candidates.clear()
    state.current_focus = None
    state.focus_history.clear()
    return {"reset": True}

def get_status() -> dict:
    return {
        "novelty_weight": state.novelty_weight,
        "social_weight": state.social_weight,
        "salience_weight": state.salience_weight,
        "candidate_count": len(state.candidates),
        "current_focus": state.current_focus,
        "recent_focus_history": state.focus_history[-10:],
    }

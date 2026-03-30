from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

from app.config import settings

GAIT_LIBRARY: Dict[str, Dict[str, Dict[str, Any]]] = {
    "canine": {
        "walk": {
            "label": "Canine Walk",
            "footfall_type": "four_beat",
            "family": "natural",
            "cadence_hint_hz": 1.4,
            "speed_range_mps": [0.2, 0.9],
            "duty_factor": 0.72,
            "bounce": "low",
            "body_carriage": "neutral",
            "notes": ["stable default gait", "good for precise navigation"],
        },
        "trot": {
            "label": "Canine Trot",
            "footfall_type": "two_beat_diagonal",
            "family": "natural",
            "cadence_hint_hz": 2.2,
            "speed_range_mps": [0.8, 1.8],
            "duty_factor": 0.55,
            "bounce": "medium",
            "body_carriage": "forward",
            "notes": ["default efficient travel gait"],
        },
        "canter": {
            "label": "Canine Canter",
            "footfall_type": "three_beat",
            "family": "natural",
            "cadence_hint_hz": 2.8,
            "speed_range_mps": [1.4, 2.6],
            "duty_factor": 0.42,
            "bounce": "medium_high",
            "body_carriage": "forward",
            "notes": ["expressive faster gait"],
        },
        "gallop": {
            "label": "Canine Gallop",
            "footfall_type": "fast_four_beat",
            "family": "natural",
            "cadence_hint_hz": 3.5,
            "speed_range_mps": [2.2, 4.5],
            "duty_factor": 0.32,
            "bounce": "high",
            "body_carriage": "aggressive_forward",
            "notes": ["high-speed mode"],
        },
        "pace": {
            "label": "Canine Pace",
            "footfall_type": "two_beat_lateral",
            "family": "variant",
            "cadence_hint_hz": 1.8,
            "speed_range_mps": [0.6, 1.3],
            "duty_factor": 0.6,
            "bounce": "low",
            "body_carriage": "stiff",
            "notes": ["useful as a style profile, not always ideal as default locomotion"],
        },
    },
    "equine": {
        "walk": {
            "label": "Equine Walk",
            "footfall_type": "four_beat",
            "family": "natural",
            "cadence_hint_hz": 1.3,
            "speed_range_mps": [0.2, 0.8],
            "duty_factor": 0.74,
            "bounce": "low",
            "body_carriage": "head_nod",
            "notes": ["four-beat walk style"],
        },
        "trot": {
            "label": "Equine Trot",
            "footfall_type": "two_beat_diagonal",
            "family": "natural",
            "cadence_hint_hz": 2.0,
            "speed_range_mps": [0.8, 1.8],
            "duty_factor": 0.52,
            "bounce": "high",
            "body_carriage": "collected_or_forward",
            "notes": ["diagonal pair movement"],
        },
        "canter": {
            "label": "Equine Canter",
            "footfall_type": "three_beat",
            "family": "natural",
            "cadence_hint_hz": 2.5,
            "speed_range_mps": [1.5, 2.8],
            "duty_factor": 0.43,
            "bounce": "rolling",
            "body_carriage": "lead_based",
            "notes": ["three-beat gait", "lope-like option"],
        },
        "gallop": {
            "label": "Equine Gallop",
            "footfall_type": "fast_four_beat",
            "family": "natural",
            "cadence_hint_hz": 3.2,
            "speed_range_mps": [2.5, 5.0],
            "duty_factor": 0.3,
            "bounce": "very_high",
            "body_carriage": "extended_forward",
            "notes": ["fast four-beat gait"],
        },
        "tolt": {
            "label": "Tölt",
            "footfall_type": "four_beat_lateral_amble",
            "family": "ambling",
            "cadence_hint_hz": 2.0,
            "speed_range_mps": [0.8, 2.5],
            "duty_factor": 0.66,
            "bounce": "very_low",
            "body_carriage": "smooth_upright",
            "notes": ["associated with Icelandic horses", "smooth four-beat lateral amble"],
        },
        "flying_pace": {
            "label": "Flying Pace / Skeið",
            "footfall_type": "two_beat_lateral_with_suspension",
            "family": "ambling",
            "cadence_hint_hz": 2.9,
            "speed_range_mps": [2.0, 4.8],
            "duty_factor": 0.36,
            "bounce": "medium",
            "body_carriage": "extended_lateral",
            "notes": ["associated with Icelandic horses", "fast lateral pace"],
        },
        "marcha_picada": {
            "label": "Marcha Picada",
            "footfall_type": "four_beat_lateral_amble",
            "family": "ambling",
            "cadence_hint_hz": 1.8,
            "speed_range_mps": [0.7, 1.8],
            "duty_factor": 0.7,
            "bounce": "very_low",
            "body_carriage": "smooth_collected",
            "notes": ["inspired by Mangalarga Marchador gait tradition"],
        },
        "running_walk": {
            "label": "Running Walk",
            "footfall_type": "four_beat_walk_pattern",
            "family": "ambling",
            "cadence_hint_hz": 1.7,
            "speed_range_mps": [0.6, 1.6],
            "duty_factor": 0.72,
            "bounce": "very_low",
            "body_carriage": "head_nod",
            "notes": ["associated with Tennessee Walking Horse style"],
        },
    },
}

@dataclass
class GaitState:
    active_profile: str = settings.default_profile
    active_gait: str = "walk"

state = GaitState()

def list_profiles() -> list[str]:
    return sorted(GAIT_LIBRARY.keys())

def list_gaits(profile: str) -> list[str]:
    return sorted(GAIT_LIBRARY.get(profile, {}).keys())

def get_gait(profile: str, gait: str) -> dict | None:
    return GAIT_LIBRARY.get(profile, {}).get(gait)

def set_active(profile: str, gait: str) -> dict:
    if profile not in GAIT_LIBRARY:
        raise KeyError(f"Unknown profile: {profile}")
    if gait not in GAIT_LIBRARY[profile]:
        raise KeyError(f"Unknown gait '{gait}' for profile '{profile}'")
    state.active_profile = profile
    state.active_gait = gait
    return {
        "active_profile": state.active_profile,
        "active_gait": state.active_gait,
        "gait": GAIT_LIBRARY[profile][gait],
    }

def get_active() -> dict:
    gait = GAIT_LIBRARY[state.active_profile][state.active_gait]
    return {
        "active_profile": state.active_profile,
        "active_gait": state.active_gait,
        "gait": gait,
    }

def adapt_command(command: dict, profile: str | None = None, gait: str | None = None) -> dict:
    chosen_profile = profile or state.active_profile
    chosen_gait = gait or state.active_gait
    gait_meta = get_gait(chosen_profile, chosen_gait)
    if not gait_meta:
        raise KeyError(f"Unknown gait '{chosen_gait}' for profile '{chosen_profile}'")
    payload = dict(command.get("payload", {}))
    speed = float(payload.get("speed_mps", gait_meta["speed_range_mps"][0]))
    adapted = {
        "type": command.get("type", "robot.command"),
        "payload": {
            **payload,
            "movement_profile": chosen_profile,
            "movement_gait": chosen_gait,
            "gait_meta": {
                "footfall_type": gait_meta["footfall_type"],
                "family": gait_meta["family"],
                "cadence_hint_hz": gait_meta["cadence_hint_hz"],
                "duty_factor": gait_meta["duty_factor"],
                "bounce": gait_meta["bounce"],
                "body_carriage": gait_meta["body_carriage"],
            },
            "recommended_speed_mps": min(max(speed, gait_meta["speed_range_mps"][0]), gait_meta["speed_range_mps"][1]),
        },
    }
    return {
        "active_profile": chosen_profile,
        "active_gait": chosen_gait,
        "gait": gait_meta,
        "adapted_command": adapted,
    }

def preview_sequence(profile: str | None = None, gait: str | None = None, seconds: float = 3.0) -> dict:
    chosen_profile = profile or state.active_profile
    chosen_gait = gait or state.active_gait
    gait_meta = get_gait(chosen_profile, chosen_gait)
    if not gait_meta:
        raise KeyError(f"Unknown gait '{chosen_gait}' for profile '{chosen_profile}'")
    cadence = gait_meta["cadence_hint_hz"]
    cycles = max(1, int(round(seconds * cadence)))
    preview = []
    for i in range(cycles):
        preview.append({
            "cycle": i + 1,
            "beat_style": gait_meta["footfall_type"],
            "body_carriage": gait_meta["body_carriage"],
            "bounce": gait_meta["bounce"],
        })
    return {
        "active_profile": chosen_profile,
        "active_gait": chosen_gait,
        "seconds": seconds,
        "estimated_cycles": cycles,
        "preview": preview,
    }

import ast
import os
from dataclasses import dataclass

def _zones():
    raw = os.getenv("DEFAULT_RESTRICTED_ZONES", "[]")
    try:
        parsed = ast.literal_eval(raw)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []

@dataclass
class Settings:
    plugin_name: str = os.getenv("PLUGIN_NAME", "sweetie-plugin-safety-governor")
    plugin_version: str = os.getenv("PLUGIN_VERSION", "1.0.0")
    default_max_speed_mps: float = float(os.getenv("DEFAULT_MAX_SPEED_MPS", "1.2"))
    default_min_human_distance_m: float = float(os.getenv("DEFAULT_MIN_HUMAN_DISTANCE_M", "0.75"))
    default_low_battery_threshold: float = float(os.getenv("DEFAULT_LOW_BATTERY_THRESHOLD", "0.20"))
    default_restricted_zones: list = None

settings = Settings()
settings.default_restricted_zones = _zones()

import os
from dataclasses import dataclass

@dataclass
class Settings:
    plugin_name: str = os.getenv("PLUGIN_NAME", "sweetie-plugin-cognitive-core")
    plugin_version: str = os.getenv("PLUGIN_VERSION", "1.0.0")
    memory_url: str = os.getenv("MEMORY_URL", "http://localhost:7000")
    action_registry_url: str = os.getenv("ACTION_REGISTRY_URL", "http://localhost:7000")
    world_model_url: str = os.getenv("WORLD_MODEL_URL", "http://localhost:7000")
    event_bus_url: str = os.getenv("EVENT_BUS_URL", "http://localhost:7000")
    default_follow_standoff_m: float = float(os.getenv("DEFAULT_FOLLOW_STANDOFF_M", "0.8"))

settings = Settings()

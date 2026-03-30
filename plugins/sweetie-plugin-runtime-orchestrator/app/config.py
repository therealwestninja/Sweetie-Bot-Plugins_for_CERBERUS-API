import os
from dataclasses import dataclass

@dataclass
class Settings:
    plugin_name: str = os.getenv("PLUGIN_NAME", "sweetie-plugin-runtime-orchestrator")
    plugin_version: str = os.getenv("PLUGIN_VERSION", "1.0.0")
    registry_url: str = os.getenv("REGISTRY_URL", "http://localhost:7000")
    world_model_url: str = os.getenv("WORLD_MODEL_URL", "http://localhost:7000")
    nav_url: str = os.getenv("NAV_URL", "http://localhost:7000")
    mission_url: str = os.getenv("MISSION_URL", "http://localhost:7000")
    sim_url: str = os.getenv("SIM_URL", "http://localhost:7000")

settings = Settings()

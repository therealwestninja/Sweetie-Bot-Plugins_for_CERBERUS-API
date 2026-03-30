import os
from dataclasses import dataclass

@dataclass
class Settings:
    plugin_name: str = os.getenv("PLUGIN_NAME", "sweetie-plugin-memory-alaya")
    plugin_version: str = os.getenv("PLUGIN_VERSION", "1.0.0")
    default_decay_per_day: float = float(os.getenv("DEFAULT_DECAY_PER_DAY", "0.04"))
    default_episodic_ttl_days: int = int(os.getenv("DEFAULT_EPISODIC_TTL_DAYS", "30"))
    default_semantic_ttl_days: int = int(os.getenv("DEFAULT_SEMANTIC_TTL_DAYS", "365"))

settings = Settings()

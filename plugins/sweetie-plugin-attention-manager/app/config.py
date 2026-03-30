import os
from dataclasses import dataclass

@dataclass
class Settings:
    plugin_name: str = os.getenv("PLUGIN_NAME", "sweetie-plugin-attention-manager")
    plugin_version: str = os.getenv("PLUGIN_VERSION", "1.0.0")
    novelty_weight: float = float(os.getenv("DEFAULT_NOVELTY_WEIGHT", "0.35"))
    social_weight: float = float(os.getenv("DEFAULT_SOCIAL_WEIGHT", "0.35"))
    salience_weight: float = float(os.getenv("DEFAULT_SALIENCE_WEIGHT", "0.30"))

settings = Settings()

import os
from dataclasses import dataclass

@dataclass
class Settings:
    plugin_name: str = os.getenv("PLUGIN_NAME", "sweetie-plugin-behavior-engine")
    plugin_version: str = os.getenv("PLUGIN_VERSION", "1.0.0")
    default_energy: float = float(os.getenv("DEFAULT_ENERGY", "0.82"))
    default_curiosity: float = float(os.getenv("DEFAULT_CURIOSITY", "0.86"))
    default_affection: float = float(os.getenv("DEFAULT_AFFECTION", "0.80"))
    default_drama: float = float(os.getenv("DEFAULT_DRAMA", "0.42"))
    default_caution: float = float(os.getenv("DEFAULT_CAUTION", "0.38"))

settings = Settings()

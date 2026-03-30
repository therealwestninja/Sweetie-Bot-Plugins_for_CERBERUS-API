import os
from dataclasses import dataclass
@dataclass
class Settings:
    plugin_name: str = os.getenv("PLUGIN_NAME","sweetie-plugin-perception-core")
    plugin_version: str = os.getenv("PLUGIN_VERSION","1.0.0")
    max_tracks: int = int(os.getenv("MAX_TRACKS","200"))
settings = Settings()

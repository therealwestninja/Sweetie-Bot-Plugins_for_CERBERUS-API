from __future__ import annotations

from typing import Dict, List

from sweetiebot.perception.models import Observation
from sweetiebot.plugins.base import PerceptionSourcePlugin


class MockPerceptionSourcePlugin(PerceptionSourcePlugin):
    plugin_id = "sweetiebot.perception.mock"

    def __init__(self) -> None:
        self.config = {
            "observations": [
                {
                    "observation_type": "presence",
                    "source": "mock_sensor",
                    "value": "guest_present",
                    "confidence": 0.9,
                    "metadata": {"zone": "front"},
                }
            ]
        }

    def manifest(self) -> Dict[str, object]:
        base = super().manifest()
        base.capabilities = ["poll_observations"]
        return base

    def configure(self, config=None) -> None:
        super().configure(config)
        if "observations" not in self.config:
            self.config["observations"] = []

    def poll_observations(self) -> List[Observation]:
        result: List[Observation] = []
        for item in self.config.get("observations", []):
            result.append(
                Observation(
                    observation_type=item["observation_type"],
                    source=item.get("source", "mock_sensor"),
                    value=item["value"],
                    confidence=float(item.get("confidence", 0.75)),
                    metadata=dict(item.get("metadata", {})),
                )
            )
        return result

    def healthcheck(self) -> Dict[str, object]:
        return {
            "healthy": True,
            "plugin_id": self.plugin_id,
            "observation_templates": len(self.config.get("observations", [])),
            "mode": "mock_polling",
        }

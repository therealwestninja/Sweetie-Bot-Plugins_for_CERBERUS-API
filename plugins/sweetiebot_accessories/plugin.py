from __future__ import annotations


class SweetieBotAccessoriesPlugin:
    name = "sweetiebot_accessories"

    def describe(self) -> dict:
        return {
            "name": self.name,
            "category": "accessories",
            "provides": [
                "capability discovery",
                "scene catalog",
                "scene application",
                "cerberus onboard audio adapter metadata",
            ],
        }

    def list_scenes(self, *, accessory_manager) -> dict:
        return {"items": accessory_manager.catalog()}

    def apply_scene(
        self,
        *,
        accessory_manager,
        scene_id: str | None,
        reason: str = "manual",
    ) -> dict:
        payload = accessory_manager.apply_scene(scene_id)
        return {
            "reason": reason,
            "scene_id": payload.get("id") if payload else None,
            "scene": payload,
        }

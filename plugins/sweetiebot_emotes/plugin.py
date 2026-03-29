from __future__ import annotations


class SweetieBotEmotesPlugin:
    name = "sweetiebot_emotes"

    def describe(self) -> dict:
        return {
            "name": self.name,
            "category": "expression",
            "provides": [
                "mood to emote mapping",
                "accessory hints",
                "timing metadata",
                "expression catalog",
            ],
        }

    def list_emotes(self, *, emote_mapper) -> dict:
        return {"items": emote_mapper.catalog()}

    def select_emote(
        self,
        *,
        emote_mapper,
        accessories_plugin,
        accessory_manager,
        character,
        persona: dict,
        mood: str,
        emote_id: str | None = None,
    ) -> dict:
        command = emote_mapper.command_for_id(emote_id) if emote_id else emote_mapper.for_mood(mood)
        profile = persona.get("defaults", {})
        scene_id = command.accessories.get("eyes") or profile.get("accessory_scene")
        accessory_scene = accessories_plugin.apply_scene(
            accessory_manager=accessory_manager,
            scene_id=scene_id,
            reason="emote",
        )
        character.active_emote = command.emote_id
        character.active_accessory_scene = accessory_scene.get("scene_id")
        payload = {
            "emote_id": command.emote_id,
            "duration_ms": command.duration_ms,
            "mood": mood,
            "tags": command.tags,
            "body_profile": command.body_profile,
            "accessories": command.accessories,
            "accessory_scene": accessory_scene,
        }
        return payload

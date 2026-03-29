from __future__ import annotations

import asyncio
from dataclasses import asdict
from pathlib import Path
from typing import Any

from plugins.sweetiebot_accessories import SweetieBotAccessoriesPlugin
from plugins.sweetiebot_attention import SweetieBotAttentionPlugin
from plugins.sweetiebot_dialogue import SweetieBotDialoguePlugin
from plugins.sweetiebot_emotes import SweetieBotEmotesPlugin
from plugins.sweetiebot_persona import SweetieBotPersonaPlugin
from plugins.sweetiebot_routines import SweetieBotRoutinesPlugin
from sweetiebot.accessories.audio_output import CerberusAudioClient
from sweetiebot.accessories.manager import AccessoryManager
from sweetiebot.character.schemas import CharacterState, MoodState
from sweetiebot.dialogue.manager import DialogueManager
from sweetiebot.dialogue.providers import (
    AnthropicMessagesProvider,
    LocalDialogueProvider,
    OpenAIResponsesProvider,
)
from sweetiebot.emotes.mapper import EmoteMapper
from sweetiebot.memory.store import MemoryStore
from sweetiebot.perception.attention_manager import AttentionManager
from sweetiebot.persona.loader import load_persona
from sweetiebot.persona.state_machine import PersonaStateMachine
from sweetiebot.routines.registry import RoutineRegistry
from upstream_api.app.config import settings
from upstream_api.app.services.events import Event, EventBus


class RuntimeState:
    """Small in-memory runtime that mirrors a CERBERUS-style plugin host."""

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[3]
        assets = root / "sweetiebot-assets"
        self.assets_root = assets
        self.event_bus = EventBus()
        self.persona_machine = PersonaStateMachine()
        self.dialogue = DialogueManager()
        self.emotes = EmoteMapper(assets / "emotes")
        self.attention = AttentionManager()
        self.memory = MemoryStore()
        self.accessories = AccessoryManager(assets / "accessories")
        self.audio_client = CerberusAudioClient(
            base_url=settings.cerberus_audio_base_url,
            speak_path=settings.cerberus_audio_path,
            bearer_token=settings.cerberus_audio_token,
            default_voice=settings.cerberus_audio_voice,
            timeout_s=settings.request_timeout_s,
        )
        self.routines = RoutineRegistry()
        self.plugins = {
            "sweetiebot_persona": SweetieBotPersonaPlugin(),
            "sweetiebot_dialogue": SweetieBotDialoguePlugin(),
            "sweetiebot_attention": SweetieBotAttentionPlugin(),
            "sweetiebot_emotes": SweetieBotEmotesPlugin(),
            "sweetiebot_routines": SweetieBotRoutinesPlugin(),
            "sweetiebot_accessories": SweetieBotAccessoriesPlugin(),
        }
        self.persona_catalog = {
            "sweetiebot_default": load_persona(assets / "persona" / "default.yaml"),
            "sweetiebot_convention": load_persona(assets / "persona" / "convention.yaml"),
            "sweetiebot_companion": load_persona(assets / "persona" / "companion.yaml"),
        }
        self.character = CharacterState(
            persona_id="sweetiebot_default",
            mood=MoodState.CURIOUS,
            attention_target=None,
            active_routine=None,
            is_speaking=False,
            active_emote=None,
            active_accessory_scene=None,
        )
        self._bootstrap_routines(assets)
        self.apply_persona("sweetiebot_default", emit=False)
        self._emit_runtime_snapshot(reason="boot")

    def _build_dialogue_provider(self):
        provider = settings.llm_provider.lower().strip()
        if provider == "openai":
            return OpenAIResponsesProvider(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                base_url=settings.openai_base_url,
                timeout_s=settings.request_timeout_s,
            )
        if provider == "anthropic":
            return AnthropicMessagesProvider(
                api_key=settings.anthropic_api_key,
                model=settings.anthropic_model,
                base_url=settings.anthropic_base_url,
                timeout_s=settings.request_timeout_s,
            )
        return LocalDialogueProvider(dialogue_manager=self.dialogue)

    def _bootstrap_routines(self, assets: Path) -> None:
        routines_dir = assets / "routines"
        for file in routines_dir.glob("*.yaml"):
            self.routines.register_from_yaml(file)

    def _emit(self, event_type: str, source: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = Event(type=event_type, source=source, payload=payload)
        self.event_bus.emit(event)
        return event.to_dict()

    def _emit_runtime_snapshot(self, reason: str) -> None:
        self._emit(
            event_type="runtime.snapshot",
            source="sweetiebot_runtime",
            payload={
                "reason": reason,
                "character": self.get_character(),
                "attention": self.get_attention(),
                "routines": self.get_routines(),
                "memory": self.get_memory_summary(),
                "accessories": self.get_accessories(),
                "personas": self.list_personas(),
                "plugins": self.get_plugins(),
                "llm": self.get_llm_status(),
                "emotes": self.get_emotes(),
            },
        )

    def subscribe_events(self) -> asyncio.Queue[dict[str, Any]]:
        return self.event_bus.subscribe()

    def unsubscribe_events(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self.event_bus.unsubscribe(queue)

    def current_persona(self) -> dict[str, Any]:
        return self.persona_catalog[self.character.persona_id]

    def list_personas(self) -> list[dict[str, Any]]:
        return self.plugins["sweetiebot_persona"].list_personas(self.persona_catalog)

    def get_persona_foundation(self) -> dict[str, Any]:
        persona = self.current_persona()
        profile = self.plugins["sweetiebot_persona"].profile_for(persona)
        return {
            "profile": profile,
            "available_emotes": self.get_emotes()["items"],
            "available_routines": self.get_routines()["items"],
            "available_accessory_scenes": self.get_accessories()["catalog"],
        }

    def get_plugins(self) -> dict[str, Any]:
        return {"items": [plugin.describe() for plugin in self.plugins.values()]}

    def get_llm_status(self) -> dict[str, Any]:
        provider = self._build_dialogue_provider()
        return {**provider.describe(), "audio": self.audio_client.describe()}

    def apply_persona(self, persona_id: str, emit: bool = True) -> dict[str, Any]:
        payload = self.plugins["sweetiebot_persona"].select_persona(
            persona_catalog=self.persona_catalog,
            persona_id=persona_id,
            dialogue_manager=self.dialogue,
            character=self.character,
        )
        scene_id = payload["persona"].get("default_accessory_scene")
        if scene_id:
            applied = self.plugins["sweetiebot_accessories"].apply_scene(
                accessory_manager=self.accessories,
                scene_id=scene_id,
                reason="persona",
            )
            payload["accessory_scene"] = applied
        if emit:
            self._emit("persona.selected", "sweetiebot_persona", payload)
        return payload

    def get_character(self) -> dict[str, Any]:
        return asdict(self.character)

    def get_attention(self) -> dict[str, Any]:
        target = self.attention.current
        return {
            "target_id": target.id if target else None,
            "confidence": target.confidence if target else 0.0,
            "mode": target.kind if target else "idle",
        }

    def get_routines(self) -> dict[str, Any]:
        active = (
            self.routines.get(self.character.active_routine)
            if self.character.active_routine
            else None
        )
        return {
            "available": self.routines.list_ids(),
            "items": self.routines.list_all(),
            "active": self.character.active_routine,
            "active_detail": active,
        }

    def get_routine_plan(self, routine_id: str) -> dict[str, Any]:
        return self.plugins["sweetiebot_routines"].plan_routine(
            routine_registry=self.routines,
            persona=self.current_persona(),
            routine_id=routine_id,
        )

    def get_emotes(self) -> dict[str, Any]:
        return self.plugins["sweetiebot_emotes"].list_emotes(emote_mapper=self.emotes)

    def say(self, text: str) -> dict[str, Any]:
        payload = self.plugins["sweetiebot_dialogue"].handle_text(
            text=text,
            dialogue_manager=self.dialogue,
            persona_machine=self.persona_machine,
            character=self.character,
            llm_provider=self._build_dialogue_provider(),
            audio_client=self.audio_client,
        )
        self._emit("dialogue.reply_ready", "sweetiebot_dialogue", payload)
        return {**payload, "mood": self.character.mood.value}

    def emote(self, emote_id: str | None = None) -> dict[str, Any]:
        payload = self.plugins["sweetiebot_emotes"].select_emote(
            emote_mapper=self.emotes,
            accessories_plugin=self.plugins["sweetiebot_accessories"],
            accessory_manager=self.accessories,
            character=self.character,
            persona=self.current_persona(),
            mood=self.character.mood.value,
            emote_id=emote_id,
        )
        payload["character"] = self.get_character()
        self._emit("persona.changed", "sweetiebot_emotes", payload)
        return payload

    def run_routine(self, routine_id: str) -> dict[str, Any]:
        payload = self.plugins["sweetiebot_routines"].start_routine(
            routine_registry=self.routines,
            persona_machine=self.persona_machine,
            character=self.character,
            persona=self.current_persona(),
            routine_id=routine_id,
        )
        self._emit("routine.started", "sweetiebot_routines", payload)
        return {
            "active": routine_id,
            "mood": self.character.mood.value,
            "title": payload["title"],
            "step_count": payload["step_count"],
            "estimated_duration_ms": payload["estimated_duration_ms"],
            "steps": payload["steps"],
        }

    def focus(
        self,
        target_id: str,
        confidence: float = 1.0,
        mode: str = "person",
    ) -> dict[str, Any]:
        payload = self.plugins["sweetiebot_attention"].focus(
            attention_manager=self.attention,
            character=self.character,
            target_id=target_id,
            confidence=confidence,
            mode=mode,
        )
        payload["attention"] = self.get_attention()
        self._emit("attention.target_changed", "sweetiebot_attention", payload)
        return self.get_attention()

    def cancel(self) -> dict[str, Any]:
        self.character.is_speaking = False
        self.character.active_routine = None
        self._emit(
            "routine.completed",
            "sweetiebot_runtime",
            {"status": "cancelled", "character": self.get_character()},
        )
        return self.get_character()

    def get_memory_summary(self) -> dict[str, Any]:
        return self.memory.summary()

    def get_accessories(self) -> dict[str, Any]:
        payload = self.accessories.capabilities()
        payload["audio"] = self.audio_client.describe()
        return payload

    def apply_accessory_scene(self, scene_id: str | None) -> dict[str, Any]:
        payload = self.plugins["sweetiebot_accessories"].apply_scene(
            accessory_manager=self.accessories,
            scene_id=scene_id,
            reason="manual",
        )
        self.character.active_accessory_scene = payload.get("scene_id")
        self._emit("accessory.scene_applied", "sweetiebot_accessories", payload)
        return payload

    def recent_events(self) -> list[dict[str, Any]]:
        return [asdict(event) for event in self.event_bus.all()[-20:]]

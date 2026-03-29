from __future__ import annotations

import asyncio
from dataclasses import asdict
from pathlib import Path
from typing import Any

from plugins.sweetiebot_attention import SweetieBotAttentionPlugin
from plugins.sweetiebot_dialogue import SweetieBotDialoguePlugin
from plugins.sweetiebot_emotes import SweetieBotEmotesPlugin
from plugins.sweetiebot_persona import SweetieBotPersonaPlugin
from plugins.sweetiebot_routines import SweetieBotRoutinesPlugin
from sweetiebot.accessories.manager import AccessoryManager
from sweetiebot.character.schemas import CharacterState, MoodState
from sweetiebot.dialogue.manager import DialogueManager
from sweetiebot.emotes.mapper import EmoteMapper
from sweetiebot.memory.store import MemoryStore
from sweetiebot.perception.attention_manager import AttentionManager
from sweetiebot.persona.loader import load_persona
from sweetiebot.persona.state_machine import PersonaStateMachine
from sweetiebot.routines.registry import RoutineRegistry
from upstream_api.app.services.events import Event, EventBus


class RuntimeState:
    """Small in-memory runtime that mirrors a CERBERUS-style plugin host."""

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[3]
        assets = root / "sweetiebot-assets"
        self.event_bus = EventBus()
        self.persona_machine = PersonaStateMachine()
        self.dialogue = DialogueManager()
        self.emotes = EmoteMapper(assets / "emotes")
        self.attention = AttentionManager()
        self.memory = MemoryStore()
        self.accessories = AccessoryManager()
        self.routines = RoutineRegistry()
        self.plugins = {
            "sweetiebot_persona": SweetieBotPersonaPlugin(),
            "sweetiebot_dialogue": SweetieBotDialoguePlugin(),
            "sweetiebot_attention": SweetieBotAttentionPlugin(),
            "sweetiebot_emotes": SweetieBotEmotesPlugin(),
            "sweetiebot_routines": SweetieBotRoutinesPlugin(),
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
        )
        self._bootstrap_routines(assets)
        self.apply_persona("sweetiebot_default", emit=False)
        self._emit_runtime_snapshot(reason="boot")

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
            },
        )

    def subscribe_events(self) -> asyncio.Queue[dict[str, Any]]:
        return self.event_bus.subscribe()

    def unsubscribe_events(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self.event_bus.unsubscribe(queue)

    def list_personas(self) -> list[dict[str, Any]]:
        return self.plugins["sweetiebot_persona"].list_personas(self.persona_catalog)

    def get_plugins(self) -> dict[str, Any]:
        return {"items": [plugin.describe() for plugin in self.plugins.values()]}

    def apply_persona(self, persona_id: str, emit: bool = True) -> dict[str, Any]:
        payload = self.plugins["sweetiebot_persona"].select_persona(
            persona_catalog=self.persona_catalog,
            persona_id=persona_id,
            dialogue_manager=self.dialogue,
            character=self.character,
        )
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

    def say(self, text: str) -> dict[str, Any]:
        payload = self.plugins["sweetiebot_dialogue"].handle_text(
            text=text,
            dialogue_manager=self.dialogue,
            persona_machine=self.persona_machine,
            character=self.character,
        )
        self._emit("dialogue.reply_ready", "sweetiebot_dialogue", payload)
        return {**payload, "mood": self.character.mood.value}

    def emote(self, emote_id: str | None = None) -> dict[str, Any]:
        payload = self.plugins["sweetiebot_emotes"].select_emote(
            emote_mapper=self.emotes,
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
            routine_id=routine_id,
        )
        self._emit("routine.started", "sweetiebot_routines", payload)
        return {
            "active": routine_id,
            "mood": self.character.mood.value,
            "title": payload["title"],
            "step_count": payload["step_count"],
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
        return self.accessories.capabilities()

    def recent_events(self) -> list[dict[str, Any]]:
        return [asdict(event) for event in self.event_bus.all()[-20:]]

from __future__ import annotations

import asyncio
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sweetiebot.accessories.manager import AccessoryManager
from sweetiebot.character.intent_types import IntentType
from sweetiebot.character.schemas import CharacterState, MoodState
from sweetiebot.dialogue.manager import DialogueManager
from sweetiebot.emotes.mapper import EmoteMapper
from sweetiebot.memory.store import MemoryStore
from sweetiebot.perception.attention_manager import AttentionManager, AttentionTarget
from sweetiebot.persona.loader import load_persona
from sweetiebot.persona.state_machine import PersonaStateMachine
from sweetiebot.routines.registry import RoutineRegistry
from upstream_api.app.services.events import Event, EventBus


class RuntimeState:
    """Tiny in-memory character runtime for scaffolding the first usable slice."""

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[3]
        assets = root / "sweetiebot-assets"
        self.event_bus = EventBus()
        self.persona_machine = PersonaStateMachine()
        self.dialogue = DialogueManager()
        self.emotes = EmoteMapper()
        self.attention = AttentionManager()
        self.memory = MemoryStore()
        self.accessories = AccessoryManager()
        self.routines = RoutineRegistry()
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
            self.routines.register(file.stem, {"id": file.stem, "path": str(file)})

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
            },
        )

    def subscribe_events(self) -> asyncio.Queue[dict[str, Any]]:
        return self.event_bus.subscribe()

    def unsubscribe_events(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self.event_bus.unsubscribe(queue)

    def list_personas(self) -> list[dict[str, Any]]:
        personas = []
        for persona in self.persona_catalog.values():
            personas.append(
                {
                    "id": persona["id"],
                    "display_name": persona.get("display_name", persona["id"]),
                    "dialogue_style": persona.get("dialogue_style", {}),
                    "motion_style": persona.get("motion_style", {}),
                    "safety_profile": persona.get("safety_profile", "unknown"),
                }
            )
        return personas

    def apply_persona(self, persona_id: str, emit: bool = True) -> dict[str, Any]:
        persona = self.persona_catalog.get(persona_id)
        if not persona:
            raise KeyError(persona_id)
        self.character.persona_id = persona_id
        self.dialogue.configure_persona(persona)
        energy_bias = persona.get("motion_style", {}).get("energy_bias", "gentle")
        if energy_bias == "showy":
            self.character.mood = MoodState.EXCITED
        elif energy_bias == "calm":
            self.character.mood = MoodState.HAPPY
        else:
            self.character.mood = MoodState.CURIOUS
        payload = {
            "persona": persona,
            "character": self.get_character(),
        }
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
        return {
            "available": self.routines.list_ids(),
            "active": self.character.active_routine,
        }

    def say(self, text: str) -> dict[str, Any]:
        reply = self.dialogue.reply_for(text)
        self.character.is_speaking = True
        trigger_map = {
            IntentType.GREET: "praised",
            IntentType.SPEAK: "music" if "sing" in text.lower() else "praised",
        }
        self.character.mood = self.persona_machine.transition(
            trigger_map.get(reply.intent, "praised")
        )
        payload = {
            "heard": text,
            "reply": reply.text,
            "intent": reply.intent.value,
            "emote_id": reply.emote_id,
            "character": self.get_character(),
        }
        self._emit("dialogue.reply_ready", "sweetiebot_dialogue", payload)
        return {
            **payload,
            "mood": self.character.mood.value,
        }

    def emote(self, emote_id: str | None = None) -> dict[str, Any]:
        command = self.emotes.for_mood(self.character.mood.value)
        selected_emote = emote_id or command.emote_id
        payload = {
            "emote_id": selected_emote,
            "mood": self.character.mood.value,
            "duration_ms": command.duration_ms,
            "character": self.get_character(),
        }
        self._emit("persona.changed", "sweetiebot_emotes", payload)
        return {
            "emote_id": selected_emote,
            "duration_ms": command.duration_ms,
            "mood": self.character.mood.value,
        }

    def run_routine(self, routine_id: str) -> dict[str, Any]:
        routine = self.routines.get(routine_id)
        if not routine:
            raise KeyError(routine_id)
        self.character.active_routine = routine_id
        self.character.mood = self.persona_machine.transition("music")
        payload = {
            "routine_id": routine_id,
            "character": self.get_character(),
        }
        self._emit("routine.started", "sweetiebot_routines", payload)
        return {"active": routine_id, "mood": self.character.mood.value}

    def focus(
        self,
        target_id: str,
        confidence: float = 1.0,
        mode: str = "person",
    ) -> dict[str, Any]:
        self.attention.update(AttentionTarget(id=target_id, kind=mode, confidence=confidence))
        self.character.attention_target = target_id
        payload = {
            "target_id": target_id,
            "confidence": confidence,
            "mode": mode,
            "character": self.get_character(),
            "attention": self.get_attention(),
        }
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

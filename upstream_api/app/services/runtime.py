from __future__ import annotations

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

    def _bootstrap_routines(self, assets: Path) -> None:
        routines_dir = assets / "routines"
        for file in routines_dir.glob("*.yaml"):
            self.routines.register(file.stem, {"id": file.stem, "path": str(file)})

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
        self.event_bus.emit(
            Event(
                type="dialogue.reply_ready",
                source="sweetiebot_dialogue",
                payload={
                    "heard": text,
                    "reply": reply.text,
                    "intent": reply.intent.value,
                    "emote_id": reply.emote_id,
                },
            )
        )
        return {
            "heard": text,
            "reply": reply.text,
            "intent": reply.intent.value,
            "emote_id": reply.emote_id,
            "mood": self.character.mood.value,
        }

    def emote(self, emote_id: str | None = None) -> dict[str, Any]:
        command = self.emotes.for_mood(self.character.mood.value)
        selected_emote = emote_id or command.emote_id
        self.event_bus.emit(
            Event(
                type="persona.changed",
                source="sweetiebot_emotes",
                payload={"emote_id": selected_emote, "mood": self.character.mood.value},
            )
        )
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
        self.event_bus.emit(
            Event(
                type="routine.started",
                source="sweetiebot_routines",
                payload={"routine_id": routine_id},
            )
        )
        return {"active": routine_id, "mood": self.character.mood.value}

    def focus(
        self,
        target_id: str,
        confidence: float = 1.0,
        mode: str = "person",
    ) -> dict[str, Any]:
        self.attention.update(AttentionTarget(id=target_id, kind=mode, confidence=confidence))
        self.character.attention_target = target_id
        self.event_bus.emit(
            Event(
                type="attention.target_changed",
                source="sweetiebot_attention",
                payload={"target_id": target_id, "confidence": confidence, "mode": mode},
            )
        )
        return self.get_attention()

    def cancel(self) -> dict[str, Any]:
        self.character.is_speaking = False
        self.character.active_routine = None
        self.event_bus.emit(
            Event(
                type="routine.completed",
                source="sweetiebot_runtime",
                payload={"status": "cancelled"},
            )
        )
        return self.get_character()

    def get_memory_summary(self) -> dict[str, Any]:
        return self.memory.summary()

    def get_accessories(self) -> dict[str, Any]:
        return self.accessories.capabilities()

    def recent_events(self) -> list[dict[str, Any]]:
        return [asdict(event) for event in self.event_bus.all()[-20:]]

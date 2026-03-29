from __future__ import annotations

from typing import Any, Dict, Optional

from sweetiebot.memory.models import MemoryRecord
from sweetiebot.plugins.base import MemoryStorePlugin
from sweetiebot.state.models import CharacterState, StateUpdate, utc_now_iso


class CharacterStateManager:
    def __init__(self, memory_store: Optional[MemoryStorePlugin] = None) -> None:
        self.memory_store = memory_store
        self.state = CharacterState()

    def snapshot(self) -> Dict[str, Any]:
        return self.state.to_dict()

    def update(self, update: StateUpdate) -> Dict[str, Any]:
        changed = False
        for field_name, value in update.__dict__.items():
            if value is not None:
                setattr(self.state, field_name, value)
                changed = True
        if changed:
            self.state.updated_at = utc_now_iso()
            self._remember("state_update", f"State updated", metadata={"state": self.state.to_dict()})
            self.state.session_event_count += 1
        return self.snapshot()

    def note_turn(self, user_text: str, reply_text: str, mood: Optional[str] = None) -> Dict[str, Any]:
        self.state.last_input = user_text
        self.state.last_reply = reply_text
        self.state.turn_count += 1
        self.state.session_event_count += 1
        if mood:
            self.state.mood = mood
        self.state.updated_at = utc_now_iso()
        self._remember("state_turn", f"Turn #{self.state.turn_count}", metadata={
            "user_text": user_text,
            "reply_text": reply_text,
            "mood": self.state.mood,
        })
        return self.snapshot()

    def set_focus(self, target: Optional[str]) -> Dict[str, Any]:
        self.state.focus_target = target
        self.state.updated_at = utc_now_iso()
        self.state.session_event_count += 1
        self._remember("focus_change", f"Focus set to {target}", metadata={"focus_target": target})
        return self.snapshot()

    def set_mood(self, mood: str) -> Dict[str, Any]:
        self.state.mood = mood
        self.state.updated_at = utc_now_iso()
        self.state.session_event_count += 1
        self._remember("mood_change", f"Mood set to {mood}", metadata={"mood": mood})
        return self.snapshot()

    def set_routine(self, routine_id: Optional[str]) -> Dict[str, Any]:
        self.state.active_routine = routine_id
        self.state.updated_at = utc_now_iso()
        self.state.session_event_count += 1
        self._remember("routine_change", f"Routine set to {routine_id}", metadata={"active_routine": routine_id})
        return self.snapshot()

    def set_emote(self, emote_id: str) -> Dict[str, Any]:
        self.state.active_emote = emote_id
        self.state.updated_at = utc_now_iso()
        self.state.session_event_count += 1
        self._remember("emote_change", f"Emote set to {emote_id}", metadata={"active_emote": emote_id})
        return self.snapshot()

    def set_accessory_scene(self, scene_id: Optional[str]) -> Dict[str, Any]:
        self.state.accessory_scene = scene_id
        self.state.updated_at = utc_now_iso()
        self.state.session_event_count += 1
        self._remember("accessory_change", f"Accessory scene set to {scene_id}", metadata={"accessory_scene": scene_id})
        return self.snapshot()

    def _remember(self, kind: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not self.memory_store:
            return
        self.memory_store.put(
            MemoryRecord(
                kind=kind,
                content=content,
                source="state_manager",
                tags=["state"],
                scope="session",
                metadata=metadata or {},
            )
        )

"""
sweetiebot.memory.context
==========================
Builds a concise context string from recent memory records so the dialogue
and behavior layers can be influenced by what has already happened this
session.

This is the memory→dialogue feedback loop described in Task 6 of the spec.
The context is injected into generate_dialogue() calls so Sweetie-Bot can:
  - Avoid repeating the same routine/emote she just did
  - Reference earlier exchanges naturally
  - Adapt mood-response based on session history
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# Max characters to include in the context block — keeps prompts bounded
_MAX_CONTEXT_CHARS = 400
_MAX_RECORDS = 10


def build_context_summary(
    records: List[Dict[str, Any]],
    *,
    current_mood: str = "calm",
    current_routine: Optional[str] = None,
    max_chars: int = _MAX_CONTEXT_CHARS,
) -> str:
    """
    Condense recent memory records into a short natural-language summary
    suitable for injecting into dialogue generation.

    Parameters
    ----------
    records:
        Recent MemoryRecord dicts (newest first is fine, order doesn't matter).
    current_mood:
        The character's current mood label.
    current_routine:
        Active routine_id if one is running.
    max_chars:
        Hard character limit on the returned string.
    """
    if not records:
        return ""

    parts: List[str] = []

    # Collect last few turns (user↔assistant dialogue)
    turns: List[str] = []
    recent_emotes: List[str] = []
    recent_routines: List[str] = []
    recent_moods: List[str] = []

    for rec in records[:_MAX_RECORDS]:
        kind = rec.get("kind", "")
        content = rec.get("content", "")

        if kind == "user_input" and content:
            turns.append('User said: ' + chr(34) + _trunc(content, 60) + chr(34))
        elif kind == "assistant_reply" and content:
            turns.append('I replied: ' + chr(34) + _trunc(content, 60) + chr(34))
        elif kind == "emote_selection" and content:
            recent_emotes.append(content)
        elif kind == "routine_arbitration" and content:
            recent_routines.append(content)
        elif kind == "mood_event" and content:
            recent_moods.append(content)

    sections: List[str] = []

    if turns:
        recent_turn_text = " → ".join(turns[-4:])  # last 2 exchanges
        sections.append(f"Recent exchange: {recent_turn_text}.")

    if recent_emotes:
        last_emote = recent_emotes[-1]
        sections.append(f"Last emote shown: {last_emote}.")

    if recent_routines:
        last_routine = recent_routines[-1]
        sections.append(f"Last routine: {last_routine}.")

    if current_routine:
        sections.append(f"Active routine: {current_routine}.")

    if recent_moods:
        sections.append(f"Mood history: {', '.join(recent_moods[-3:])}.")

    sections.append(f"Current mood: {current_mood}.")

    summary = " ".join(sections)
    if len(summary) > max_chars:
        summary = summary[:max_chars].rsplit(" ", 1)[0] + "…"

    return summary


def extract_recent_commands(
    records: List[Dict[str, Any]],
    *,
    limit: int = 5,
) -> Dict[str, List[str]]:
    """
    Extract recently used routine / emote IDs from memory.

    Useful for the BehaviorDirector to avoid repeating the same action.
    Returns ``{"routines": [...], "emotes": [...]}`` (most recent first).
    """
    routines: List[str] = []
    emotes: List[str] = []

    for rec in records:
        kind = rec.get("kind", "")
        meta = rec.get("metadata", {})

        if kind == "routine_arbitration":
            rid = meta.get("requested_routine") or meta.get("routine_id")
            if rid and rid not in routines:
                routines.append(rid)

        elif kind == "emote_selection":
            eid = rec.get("content") or meta.get("emote_id")
            if eid and eid not in emotes:
                emotes.append(eid)

        if len(routines) >= limit and len(emotes) >= limit:
            break

    return {"routines": routines[:limit], "emotes": emotes[:limit]}


def _trunc(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"

"""
sweetiebot.behavior.nudge_handler
===================================
Handles "gentle nudge" inputs from the Companion Web Interface.

Philosophy (from sweetie-bot-project / FlexBE pattern)
-------------------------------------------------------
The operator can *suggest* — not command. Every nudge arrives as an
intent.  Sweetie-Bot reacts immediately with a micro-reaction (verbal +
physical), then runs the decision matrix to decide what to do next.

This mirrors how a real animal responds to a tap: it acknowledges first,
then chooses to comply, adapt, or continue what it was doing.

Nudge types
-----------
  attention  — gentle tap to get attention ("Hello?")
  interaction — friendly touch / wave ("Oh, hi!")
  interrupt  — persistent/annoying interruption ("Hey, quit it!")
  physical   — unexpected poke / jostle ("Oof~!")
  encourage  — praise/approval signal (happy wag)
  calm       — "settle down" signal (returns to neutral)

Decision matrix
---------------
Rows: current character state (idle, active_routine, safe_mode, degraded)
Cols: nudge type (attention, interaction, interrupt, physical, encourage, calm)
Cell: AutonomyDecision (comply / adapt / resist / continue)

Weights are soft — the matrix produces a scored decision, not a hard rule.
The character can "resist" an interrupt if it's mid-routine, for example,
which feels more natural than instant compliance.

Output
------
NudgeResult:
  micro_reaction   — immediate verbal + emote + micro-motion (always fires)
  autonomy_decision — what Sweetie-Bot decides to do next
  suggested_action  — optional follow-on suggestion (routed through safety gate)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Nudge types
# ---------------------------------------------------------------------------

class NudgeType(StrEnum):
    ATTENTION   = "attention"    # tap to get attention
    INTERACTION = "interaction"  # friendly touch / wave
    INTERRUPT   = "interrupt"    # persistent nudge to stop something
    PHYSICAL    = "physical"     # unexpected poke / jostle
    ENCOURAGE   = "encourage"    # praise / approval
    CALM        = "calm"         # "settle down" signal


class AutonomyDecision(StrEnum):
    COMPLY   = "comply"    # do what the nudge suggests
    ADAPT    = "adapt"     # acknowledge and blend it in gracefully
    RESIST   = "resist"    # politely continue current activity
    CONTINUE = "continue"  # acknowledge but keep doing what I was doing


# ---------------------------------------------------------------------------
# Micro-reaction library
# Maps NudgeType → immediate character response
# ---------------------------------------------------------------------------

@dataclass
class MicroReaction:
    speech: str          # what Sweetie-Bot says
    emote: str           # emote_id (passes through emote mapper)
    motion_hint: Optional[str]   # optional micro-motion (may be skipped if busy)
    accessory: Optional[str]     # accessory scene change
    priority: int = 5    # 1 = urgent, 10 = low

    def to_dict(self) -> Dict[str, Any]:
        return {
            "speech": self.speech,
            "emote": self.emote,
            "motion_hint": self.motion_hint,
            "accessory": self.accessory,
            "priority": self.priority,
        }


_MICRO_REACTIONS: Dict[NudgeType, List[MicroReaction]] = {
    NudgeType.ATTENTION: [
        MicroReaction(
            speech="Hello?",
            emote="curious_headtilt",
            motion_hint=None,
            accessory="eyes_curious",
            priority=6,
        ),
        MicroReaction(
            speech="Hmm? Did you need me?",
            emote="curious_headtilt",
            motion_hint=None,
            accessory="eyes_curious",
            priority=6,
        ),
    ],
    NudgeType.INTERACTION: [
        MicroReaction(
            speech="Oh, hi!",
            emote="warm_smile",
            motion_hint="greeting_01",
            accessory="eyes_happy",
            priority=5,
        ),
        MicroReaction(
            speech="Oh hey there!",
            emote="happy_bounce",
            motion_hint=None,
            accessory="eyes_happy",
            priority=5,
        ),
    ],
    NudgeType.INTERRUPT: [
        MicroReaction(
            speech="Hey, quit it!",
            emote="bashful_shift",
            motion_hint=None,
            accessory="eyes_neutral",
            priority=3,
        ),
        MicroReaction(
            speech="I'm trying to focus here~",
            emote="bashful_shift",
            motion_hint=None,
            accessory="eyes_neutral",
            priority=3,
        ),
    ],
    NudgeType.PHYSICAL: [
        MicroReaction(
            speech="Oof~!",
            emote="bashful_shift",
            motion_hint=None,
            accessory="eyes_curious",
            priority=2,
        ),
        MicroReaction(
            speech="Whoa!",
            emote="curious_headtilt",
            motion_hint=None,
            accessory="eyes_curious",
            priority=2,
        ),
    ],
    NudgeType.ENCOURAGE: [
        MicroReaction(
            speech="Yay! Thank you!",
            emote="happy_bounce",
            motion_hint=None,
            accessory="eyes_happy",
            priority=6,
        ),
    ],
    NudgeType.CALM: [
        MicroReaction(
            speech="Okay, settling down.",
            emote="calm_neutral",
            motion_hint="return_to_neutral",
            accessory="eyes_neutral",
            priority=4,
        ),
    ],
}


# ---------------------------------------------------------------------------
# Decision matrix
# ---------------------------------------------------------------------------
# Rows: robot state category
# Cols: nudge type
# Value: AutonomyDecision
#
# Reading the matrix: "If I'm [state] and I get a [nudge], I [decision]"
#
# Key design choices:
# - Physical nudges always get ADAPT (acknowledge the jostle, don't ignore)
# - Interrupt nudges while mid-routine → RESIST (don't break immersion)
# - Safe/degraded modes always COMPLY with calm nudges (safety priority)
# - Encourage always gets CONTINUE (don't stop because someone cheered)

_DECISION_MATRIX: Dict[str, Dict[NudgeType, AutonomyDecision]] = {
    "idle": {
        NudgeType.ATTENTION:   AutonomyDecision.COMPLY,
        NudgeType.INTERACTION: AutonomyDecision.COMPLY,
        NudgeType.INTERRUPT:   AutonomyDecision.ADAPT,
        NudgeType.PHYSICAL:    AutonomyDecision.ADAPT,
        NudgeType.ENCOURAGE:   AutonomyDecision.CONTINUE,
        NudgeType.CALM:        AutonomyDecision.COMPLY,
    },
    "active_routine": {
        NudgeType.ATTENTION:   AutonomyDecision.ADAPT,    # headtilt but keep going
        NudgeType.INTERACTION: AutonomyDecision.ADAPT,    # acknowledge, finish routine
        NudgeType.INTERRUPT:   AutonomyDecision.RESIST,   # "I'm doing something!"
        NudgeType.PHYSICAL:    AutonomyDecision.ADAPT,    # react but continue
        NudgeType.ENCOURAGE:   AutonomyDecision.CONTINUE, # keep going!
        NudgeType.CALM:        AutonomyDecision.COMPLY,   # always listen to calm
    },
    "safe_mode": {
        NudgeType.ATTENTION:   AutonomyDecision.COMPLY,
        NudgeType.INTERACTION: AutonomyDecision.ADAPT,
        NudgeType.INTERRUPT:   AutonomyDecision.COMPLY,   # in safe mode, be compliant
        NudgeType.PHYSICAL:    AutonomyDecision.COMPLY,
        NudgeType.ENCOURAGE:   AutonomyDecision.CONTINUE,
        NudgeType.CALM:        AutonomyDecision.COMPLY,
    },
    "degraded": {
        NudgeType.ATTENTION:   AutonomyDecision.ADAPT,
        NudgeType.INTERACTION: AutonomyDecision.ADAPT,
        NudgeType.INTERRUPT:   AutonomyDecision.COMPLY,
        NudgeType.PHYSICAL:    AutonomyDecision.COMPLY,
        NudgeType.ENCOURAGE:   AutonomyDecision.CONTINUE,
        NudgeType.CALM:        AutonomyDecision.COMPLY,
    },
}

# How each decision maps to a follow-on action suggestion
_DECISION_ACTIONS: Dict[AutonomyDecision, Dict[NudgeType, Optional[str]]] = {
    AutonomyDecision.COMPLY: {
        NudgeType.ATTENTION:   "process_dialogue",
        NudgeType.INTERACTION: "greet_guest",
        NudgeType.INTERRUPT:   "return_to_neutral",
        NudgeType.PHYSICAL:    None,
        NudgeType.ENCOURAGE:   None,
        NudgeType.CALM:        "return_to_neutral",
    },
    AutonomyDecision.ADAPT: {
        NudgeType.ATTENTION:   None,         # just react, then continue
        NudgeType.INTERACTION: None,
        NudgeType.INTERRUPT:   None,
        NudgeType.PHYSICAL:    None,
        NudgeType.ENCOURAGE:   None,
        NudgeType.CALM:        "return_to_neutral",
    },
    AutonomyDecision.RESIST: {
        NudgeType.ATTENTION:   None,
        NudgeType.INTERACTION: None,
        NudgeType.INTERRUPT:   None,         # keep current routine
        NudgeType.PHYSICAL:    None,
        NudgeType.ENCOURAGE:   None,
        NudgeType.CALM:        None,
    },
    AutonomyDecision.CONTINUE: {
        NudgeType.ATTENTION:   None,
        NudgeType.INTERACTION: None,
        NudgeType.INTERRUPT:   None,
        NudgeType.PHYSICAL:    None,
        NudgeType.ENCOURAGE:   None,
        NudgeType.CALM:        None,
    },
}


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class NudgeResult:
    nudge_type: NudgeType
    micro_reaction: MicroReaction
    autonomy_decision: AutonomyDecision
    suggested_action: Optional[str]     # route through safety gate
    state_category: str
    nudge_count_recent: int             # how many nudges in the last window
    suppressed: bool = False            # True if nudge was spam-suppressed
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nudge_type": self.nudge_type.value,
            "micro_reaction": self.micro_reaction.to_dict(),
            "autonomy_decision": self.autonomy_decision.value,
            "suggested_action": self.suggested_action,
            "state_category": self.state_category,
            "nudge_count_recent": self.nudge_count_recent,
            "suppressed": self.suppressed,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# NudgeHandler
# ---------------------------------------------------------------------------

class NudgeHandler:
    """
    Processes operator nudges from the Companion Web Interface.

    Nudges are gentle suggestions — not commands.  The handler:
    1. Validates and classifies the nudge
    2. Selects an immediate micro-reaction (always fires)
    3. Runs the decision matrix to decide what to do next
    4. Returns a NudgeResult for the runtime to execute

    Anti-spam:
    Consecutive nudges of the same type escalate: attention → interaction → interrupt.
    More than max_recent_nudges in the spam_window seconds → micro-reaction only,
    no suggested_action (Sweetie-Bot gets mildly annoyed but doesn't break).

    Parameters
    ----------
    spam_window_seconds:
        Rolling window for nudge count tracking.
    max_nudges_before_suppress:
        If this many nudges arrive in the window, suppress suggested_action.
    """

    def __init__(
        self,
        *,
        spam_window_seconds: float = 10.0,
        max_nudges_before_suppress: int = 4,
    ) -> None:
        self._spam_window = spam_window_seconds
        self._max_nudges = max_nudges_before_suppress
        self._nudge_history: List[tuple[float, NudgeType]] = []
        self._reaction_index: Dict[NudgeType, int] = {}  # rotating response variety

    def handle(
        self,
        nudge_type: NudgeType | str,
        *,
        current_mood: str = "calm",
        active_routine: Optional[str] = None,
        safe_mode: bool = False,
        degraded_mode: bool = False,
    ) -> NudgeResult:
        """
        Process a single nudge from the operator.

        Parameters
        ----------
        nudge_type:
            The type of nudge (NudgeType enum or string).
        current_mood:
            Current character mood (influences reaction variety).
        active_routine:
            Currently running routine, if any.
        safe_mode / degraded_mode:
            Current safety flags.
        """
        # Normalise nudge type
        try:
            ntype = NudgeType(nudge_type) if isinstance(nudge_type, str) else nudge_type
        except ValueError:
            ntype = NudgeType.ATTENTION
            log.warning("NudgeHandler: unknown nudge type %r, defaulting to attention", nudge_type)

        # Record and get spam count
        self._record_nudge(ntype)
        recent_count = self._count_recent(ntype)

        # Determine state category
        state = self._categorise_state(
            active_routine=active_routine,
            safe_mode=safe_mode,
            degraded_mode=degraded_mode,
        )

        # Pick micro-reaction (rotate through variety)
        reaction = self._pick_reaction(ntype, current_mood)

        # Check spam suppression
        suppressed = recent_count > self._max_nudges
        if suppressed:
            # Escalate to mild annoyance reaction
            reaction = MicroReaction(
                speech="Hey, quit it!" if recent_count % 2 == 0 else "I said quit it~!",
                emote="bashful_shift",
                motion_hint=None,
                accessory="eyes_neutral",
                priority=2,
            )
            log.info("NudgeHandler: spam suppression active, count=%d", recent_count)

        # Decision matrix lookup
        matrix_row = _DECISION_MATRIX.get(state, _DECISION_MATRIX["idle"])
        decision = matrix_row.get(ntype, AutonomyDecision.ADAPT)

        # Resolve follow-on action
        suggested_action: Optional[str] = None
        if not suppressed:
            action_row = _DECISION_ACTIONS.get(decision, {})
            suggested_action = action_row.get(ntype)

        notes = [f"state={state} decision={decision.value}"]
        if suppressed:
            notes.append(f"spam suppressed after {recent_count} nudges in {self._spam_window}s")

        result = NudgeResult(
            nudge_type=ntype,
            micro_reaction=reaction,
            autonomy_decision=decision,
            suggested_action=suggested_action,
            state_category=state,
            nudge_count_recent=recent_count,
            suppressed=suppressed,
            notes=notes,
        )

        log.info(
            "NudgeHandler: type=%s state=%s decision=%s action=%s suppressed=%s",
            ntype.value, state, decision.value, suggested_action, suppressed,
        )
        return result

    def recent_nudges(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recent nudge history for observability."""
        now = time.monotonic()
        return [
            {"type": t.value, "ago_seconds": round(now - ts, 1)}
            for ts, t in reversed(self._nudge_history[-limit:])
        ]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "spam_window_seconds": self._spam_window,
            "max_nudges_before_suppress": self._max_nudges,
            "nudge_history_size": len(self._nudge_history),
            "recent_nudges": self.recent_nudges(limit=5),
        }

    # ── Internal ───────────────────────────────────────────────────────

    def _record_nudge(self, ntype: NudgeType) -> None:
        now = time.monotonic()
        self._nudge_history.append((now, ntype))
        # Trim old entries
        cutoff = now - self._spam_window
        self._nudge_history = [(ts, t) for ts, t in self._nudge_history if ts > cutoff]

    def _count_recent(self, ntype: NudgeType) -> int:
        now = time.monotonic()
        cutoff = now - self._spam_window
        return sum(1 for ts, t in self._nudge_history if ts > cutoff and t == ntype)

    def _categorise_state(
        self,
        active_routine: Optional[str],
        safe_mode: bool,
        degraded_mode: bool,
    ) -> str:
        if degraded_mode:
            return "degraded"
        if safe_mode:
            return "safe_mode"
        if active_routine and active_routine != "return_to_neutral":
            return "active_routine"
        return "idle"

    def _pick_reaction(self, ntype: NudgeType, mood: str) -> MicroReaction:
        """Rotate through available reactions for variety."""
        reactions = _MICRO_REACTIONS.get(ntype, [_MICRO_REACTIONS[NudgeType.ATTENTION][0]])
        idx = self._reaction_index.get(ntype, 0)
        reaction = reactions[idx % len(reactions)]
        self._reaction_index[ntype] = (idx + 1) % len(reactions)

        # Mood modulation: excited mood boosts happy reactions
        if mood in ("excited", "happy") and ntype == NudgeType.INTERACTION:
            return MicroReaction(
                speech="Oh hi hi hi!!",
                emote="happy_bounce",
                motion_hint="idle_cute",
                accessory="eyes_happy",
                priority=5,
            )

        return reaction

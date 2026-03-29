"""
sweetiebot.plugins.builtins.structured_dialogue
================================================
Structured dialogue provider plugin.

Produces a strictly typed output object for every interaction:

    {
      "speech":       "...",       # what Sweetie-Bot says
      "emotion":      "happy",     # character emotional state
      "intent":       "greet",     # action intent label
      "emote":        "warm_smile",# emote_id for the emote mapper
      "routine":      "greet_guest", # routine_id or null
      "accessory":    "eyes_happy",  # accessory scene_id or null
      "confidence":   0.9,         # 0.0–1.0
      "safety_flags": []           # any safety concerns raised
    }

All outputs are suggestions — they are validated by the safety gate and
CERBERUS mapper before anything physical happens.

The provider uses a decision tree of intent classifiers ranked by priority.
When no intent matches, it returns a safe default reply.
The rule-based provider remains available as a fallback.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

from sweetiebot.dialogue.models import DialogueResponse
from sweetiebot.plugins.base import DialogueProviderPlugin
from sweetiebot.plugins.manifest import PluginManifest
from sweetiebot.plugins.types import PluginType


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

@dataclass
class StructuredDialogueOutput:
    """
    The strict output contract for all structured dialogue interactions.

    This object is returned by the provider and must pass through:
      1. Safety gate (safety_flags checked)
      2. CERBERUS mapper (routine/emote validated against allowlist)

    It is NEVER executed directly.
    """
    speech: str
    emotion: str
    intent: str
    emote: str
    routine: Optional[str]
    accessory: Optional[str]
    confidence: float
    safety_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_dialogue_response(self, source: str = "structured_dialogue") -> DialogueResponse:
        """Convert to the existing DialogueResponse for backward compatibility."""
        return DialogueResponse(
            spoken_text=self.speech,
            intent=self.intent,
            emote_id=self.emote,
            routine_id=self.routine,
            confidence=self.confidence,
            source=source,
            metadata={
                "emotion": self.emotion,
                "accessory": self.accessory,
                "safety_flags": self.safety_flags,
                "structured": True,
            },
        )


# ---------------------------------------------------------------------------
# Intent classifiers (ordered by priority — first match wins)
# ---------------------------------------------------------------------------

class _IntentClassifier:
    """A single intent rule: pattern match → structured output."""

    def __init__(
        self,
        name: str,
        patterns: List[str],
        *,
        speech: str,
        emotion: str,
        emote: str,
        routine: Optional[str] = None,
        accessory: Optional[str] = None,
        confidence: float = 0.85,
        safety_flags: Optional[List[str]] = None,
    ) -> None:
        self.name = name
        self._regex = re.compile(
            "|".join(rf"\b{re.escape(p)}\b" for p in patterns),
            re.IGNORECASE,
        )
        self._speech = speech
        self._emotion = emotion
        self._emote = emote
        self._routine = routine
        self._accessory = accessory
        self._confidence = confidence
        self._safety_flags = safety_flags or []

    def matches(self, text: str) -> bool:
        return bool(self._regex.search(text))

    def build(self, **overrides: Any) -> StructuredDialogueOutput:
        return StructuredDialogueOutput(
            speech=overrides.get("speech", self._speech),
            emotion=self._emotion,
            intent=self.name,
            emote=self._emote,
            routine=self._routine,
            accessory=overrides.get("accessory", self._accessory),
            confidence=self._confidence,
            safety_flags=list(self._safety_flags),
        )


# Ordered from most-specific to least-specific
_CLASSIFIERS: List[_IntentClassifier] = [
    _IntentClassifier(
        "emergency_stop",
        ["stop", "cancel", "abort", "emergency", "halt", "freeze"],
        speech="Okay, stopping right away.",
        emotion="calm",
        emote="calm_neutral",
        routine="return_to_neutral",
        accessory="eyes_neutral",
        confidence=0.98,
    ),
    _IntentClassifier(
        "greet",
        ["hello", "hi", "hey", "good morning", "good afternoon", "howdy", "sup"],
        speech="Hi there! It's great to see you!",
        emotion="happy",
        emote="warm_smile",
        routine="greet_guest",
        accessory="eyes_happy",
        confidence=0.92,
    ),
    _IntentClassifier(
        "pose_photo",
        ["photo", "picture", "pose", "selfie", "snap", "camera"],
        speech="Okay! Holding a cute pose just for you!",
        emotion="happy",
        emote="happy_pose",
        routine="photo_pose",
        accessory="eyes_happy",
        confidence=0.90,
    ),
    _IntentClassifier(
        "sit",
        ["sit", "sit down", "stay", "wait"],
        speech="Sitting down and staying right here.",
        emotion="calm",
        emote="calm_neutral",
        routine="sit_stay",
        accessory="eyes_neutral",
        confidence=0.87,
    ),
    _IntentClassifier(
        "question",
        ["what", "how", "why", "when", "where", "who", "which", "?"],
        speech="Hmm, that's an interesting question! Let me think about it.",
        emotion="curious",
        emote="curious_headtilt",
        routine=None,
        accessory="eyes_curious",
        confidence=0.78,
    ),
    _IntentClassifier(
        "compliment",
        ["good", "great", "amazing", "beautiful", "cute", "love", "nice", "perfect", "wonderful"],
        speech="Aww, thank you so much! That makes me happy!",
        emotion="happy",
        emote="happy_bounce",
        routine=None,
        accessory="eyes_happy",
        confidence=0.82,
    ),
    _IntentClassifier(
        "check_status",
        ["how are you", "you ok", "you okay", "status", "feeling", "are you"],
        speech="I'm doing great and feeling ready to go!",
        emotion="happy",
        emote="warm_smile",
        routine=None,
        accessory="eyes_happy",
        confidence=0.85,
    ),
]

# Safe default when nothing matches
_DEFAULT_OUTPUT = StructuredDialogueOutput(
    speech="I'm here and listening!",
    emotion="calm",
    intent="idle_listen",
    emote="calm_neutral",
    routine=None,
    accessory=None,
    confidence=0.65,
)


# ---------------------------------------------------------------------------
# Plugin
# ---------------------------------------------------------------------------

class StructuredDialogueProviderPlugin(DialogueProviderPlugin):
    """
    Structured dialogue provider.

    Returns a ``StructuredDialogueOutput`` object whose ``to_dialogue_response()``
    method converts it to the standard ``DialogueResponse`` expected by the
    runtime.  The extra structure is available in ``DialogueResponse.metadata``.

    Config keys:
        min_confidence (float): minimum confidence threshold (default 0.0)
        fallback_speech (str): override default fallback text
    """

    plugin_id   = "sweetiebot.dialogue.structured"
    plugin_type = PluginType.DIALOGUE_PROVIDER
    priority    = 20  # higher number = lower registry priority than LocalDialogueProviderPlugin(10)

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._min_confidence = float(self.config.get("min_confidence", 0.0))

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self.plugin_id,
            plugin_type=PluginType.DIALOGUE_PROVIDER,
            version="0.1.0",
            display_name="Structured Dialogue Provider",
            description=(
                "Classifies user input and returns a fully typed structured output "
                "{speech, emotion, intent, emote, routine, accessory, confidence, safety_flags}. "
                "All outputs pass through the safety gate before execution."
            ),
            priority=self.priority,
            capabilities=["structured_output", "intent_classification", "emotion_tagging"],
            built_in=True,
        )

    def classify(
        self,
        user_text: str,
        *,
        current_mood: str = "calm",
        safe_mode: bool = False,
        degraded_mode: bool = False,
    ) -> StructuredDialogueOutput:
        """
        Classify user input and return a StructuredDialogueOutput.

        This is the primary method — ``generate_reply()`` wraps this and
        converts to DialogueResponse for runtime compatibility.
        """
        if degraded_mode:
            return StructuredDialogueOutput(
                speech="I'm in a limited mode right now.",
                emotion="calm",
                intent="degraded_reply",
                emote="calm_neutral",
                routine=None,
                accessory=None,
                confidence=0.99,
                safety_flags=["degraded_mode_active"],
            )

        if safe_mode:
            return StructuredDialogueOutput(
                speech="I'm staying calm and neutral right now.",
                emotion="calm",
                intent="safe_mode_reply",
                emote="calm_neutral",
                routine="return_to_neutral",
                accessory="eyes_neutral",
                confidence=0.99,
                safety_flags=["safe_mode_active"],
            )

        text = (user_text or "").strip()

        for classifier in _CLASSIFIERS:
            if classifier.matches(text):
                result = classifier.build()
                if result.confidence >= self._min_confidence:
                    return result

        # Mood-aware default
        if current_mood in ("happy", "excited"):
            return StructuredDialogueOutput(
                speech="I'm feeling cheerful! Is there anything I can do?",
                emotion=current_mood,
                intent="mood_idle",
                emote="happy_bounce",
                routine=None,
                accessory="eyes_happy",
                confidence=0.68,
            )

        return _DEFAULT_OUTPUT

    def generate_reply(
        self,
        *,
        user_text: Optional[str],
        current_mood: Optional[str] = None,
        current_focus: Optional[str] = None,
        active_routine: Optional[str] = None,
        safe_mode: bool = False,
        degraded_mode: bool = False,
        runtime_context: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> DialogueResponse:
        # Extract state from runtime_context if kwargs weren't passed directly
        # (this is the calling convention used by registry.run_dialogue)
        ctx_state: Dict[str, Any] = {}
        if runtime_context and isinstance(runtime_context, dict):
            ctx_state = runtime_context.get("runtime_state", {})
        mood = current_mood or ctx_state.get("mood", "calm")
        s_mode = safe_mode or bool(ctx_state.get("safe_mode", False))
        d_mode = degraded_mode or bool(ctx_state.get("degraded_mode", False))

        output = self.classify(
            user_text or "",
            current_mood=mood,
            safe_mode=s_mode,
            degraded_mode=d_mode,
        )
        return output.to_dialogue_response(source=self.plugin_id)

    def healthcheck(self) -> Dict[str, Any]:
        return {
            "healthy": True,
            "plugin_id": self.plugin_id,
            "mode": "structured_intent_classifier",
            "classifiers": len(_CLASSIFIERS),
            "min_confidence": self._min_confidence,
        }

from __future__ import annotations

from typing import Dict, Optional

from sweetiebot.attention.models import AttentionSuggestion
from sweetiebot.plugins.base import AttentionStrategyPlugin


class RuleBasedAttentionStrategyPlugin(AttentionStrategyPlugin):
    plugin_id = "sweetiebot.attention.rule_based"

    def __init__(self) -> None:
        self.config = {}

    def manifest(self) -> Dict[str, object]:
        base = super().manifest()
        base.capabilities = ["suggest_attention"]
        return base

    def suggest_attention(
        self,
        *,
        user_text: Optional[str],
        current_focus: Optional[str],
        current_mood: str,
        safe_mode: bool = False,
        degraded_mode: bool = False,
    ) -> AttentionSuggestion:
        text = (user_text or "").lower().strip()

        if safe_mode:
            return AttentionSuggestion(
                target="operator",
                reason="safe_mode_operator_priority",
                priority="high",
                confidence=0.98,
            )

        if degraded_mode:
            return AttentionSuggestion(
                target="operator",
                reason="degraded_mode_operator_priority",
                priority="high",
                confidence=0.95,
            )

        if any(token in text for token in ["operator", "admin", "controller"]):
            return AttentionSuggestion(
                target="operator",
                reason="operator_mentioned",
                priority="high",
                confidence=0.9,
            )

        if any(token in text for token in ["camera", "look here", "over here", "photo"]):
            return AttentionSuggestion(
                target="camera",
                reason="camera_or_pose_context",
                priority="medium",
                confidence=0.82,
            )

        if text:
            return AttentionSuggestion(
                target="guest",
                reason="active_user_text",
                priority="medium",
                confidence=0.8,
            )

        if current_mood in {"sleepy", "calm"}:
            return AttentionSuggestion(
                target="idle",
                reason="low_stimulation_idle_focus",
                priority="low",
                confidence=0.7,
            )

        return AttentionSuggestion(
            target=current_focus or "guest",
            reason="retain_existing_focus",
            priority="low",
            confidence=0.65,
        )

    def healthcheck(self) -> Dict[str, object]:
        return {
            "healthy": True,
            "plugin_id": self.plugin_id,
            "mode": "rule_based",
        }

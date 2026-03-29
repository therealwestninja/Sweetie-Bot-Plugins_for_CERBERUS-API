"""
sweetiebot.plugins.builtins.cerberus
=====================================
Built-in plugin implementations for the Sweetie-Bot ↔ CERBERUS integration layer.

Three plugins are provided:

AllowlistCerberusMapperPlugin
    Wraps ``CerberusMapper``. Translates ``CharacterResponse`` objects into
    ``IntegrationPlan`` objects using a statically configured allowlist of
    routine, emote, and accessory IDs. Supports dry-run mode and hot-reload
    of mapping tables via ``configure()``.

    plugin_id: ``sweetiebot.integration.allowlist_mapper``
    plugin_type: ``cerberus_mapper``

RuleBasedSafetyGatePlugin
    Wraps ``SafetyGate``. Enforces per-routine-ID cooldowns, operating-mode
    restrictions (NORMAL/SAFE/DEGRADED/EMERGENCY), and operator overrides.
    Maintains an audit log of recent gate decisions.

    plugin_id: ``sweetiebot.integration.safety_gate``
    plugin_type: ``safety_gate``

MemoryContextBuilderPlugin
    Wraps ``build_context_summary`` and ``extract_recent_commands`` from
    ``sweetiebot.memory.context``. Converts raw memory records into a
    natural-language context string injected into dialogue generation.

    plugin_id: ``sweetiebot.memory.context_builder``
    plugin_type: ``memory_context``

All three are registered in ``register_builtins()`` so any project using
Sweetie-Bot gets the integration layer for free.  Override by registering a
higher-priority plugin of the same type before calling ``register_builtins()``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sweetiebot.integration.cerberus_mapper import CerberusMapper
from sweetiebot.integration.schemas import SafetyMode
from sweetiebot.memory.context import build_context_summary, extract_recent_commands
from sweetiebot.plugins.base import (
    CerberusMapperPlugin,
    MemoryContextPlugin,
    SafetyGatePlugin,
)
from sweetiebot.plugins.health import PluginHealthCheck, PluginHealthStatus
from sweetiebot.plugins.manifest import PluginManifest
from sweetiebot.plugins.types import PluginType
from sweetiebot.safety.gate import SafetyGate


# ---------------------------------------------------------------------------
# AllowlistCerberusMapperPlugin
# ---------------------------------------------------------------------------

class AllowlistCerberusMapperPlugin(CerberusMapperPlugin):
    """
    Maps ``CharacterResponse`` → ``IntegrationPlan`` using an allowlist.

    Config keys (all optional — defaults match the built-in mapping tables):
        dry_run (bool):
            If True, all plans are marked non-executable. Default: False.
        extra_routines (list[dict]):
            Additional routine mapping entries to merge on top of the defaults.
        extra_emotes (list[dict]):
            Additional emote mapping entries.
        extra_accessories (list[dict]):
            Additional accessory scene mapping entries.

    Example plugin config (YAML):
        plugins:
          sweetiebot.integration.allowlist_mapper:
            dry_run: false
            extra_routines:
              - routine_id: spin_in_place
                cerberus_command: sport.spin_360
                description: "Full 360 spin on the spot"
                estimated_duration_ms: 3000
                tags: [performance]
    """

    plugin_id   = "sweetiebot.integration.allowlist_mapper"
    plugin_type = PluginType.CERBERUS_MAPPER
    priority    = 10  # lowest number = highest priority

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._mapper = CerberusMapper(
            dry_run=bool(self.config.get("dry_run", False)),
            extra_routines=self.config.get("extra_routines"),
            extra_emotes=self.config.get("extra_emotes"),
            extra_accessories=self.config.get("extra_accessories"),
        )

    def configure(self, config: Dict[str, Any] | None = None) -> None:
        super().configure(config)
        if config:
            self._mapper.reload_mappings(
                routines=config.get("extra_routines"),
                emotes=config.get("extra_emotes"),
                accessories=config.get("extra_accessories"),
            )
            if "dry_run" in config:
                self._mapper.dry_run = bool(config["dry_run"])

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self.plugin_id,
            plugin_type=PluginType.CERBERUS_MAPPER,
            version="0.1.1",
            display_name="Allowlist CERBERUS Mapper",
            description=(
                "Translates CharacterResponse objects into CERBERUS IntegrationPlans "
                "using a statically configured allowlist. Fail-closed: unknown IDs are rejected."
            ),
            priority=self.priority,
            capabilities=["allowlist_routines", "allowlist_emotes", "allowlist_accessories", "dry_run"],
            built_in=True,
            config_schema={
                "dry_run": {"type": "boolean", "default": False},
                "extra_routines": {"type": "array"},
                "extra_emotes":   {"type": "array"},
                "extra_accessories": {"type": "array"},
            },
        )

    # ── CerberusMapperPlugin interface ─────────────────────────────────

    def plan(
        self,
        response: Any,
        *,
        safety_mode: Any = None,
        dry_run: Optional[bool] = None,
    ) -> Any:
        effective_mode = safety_mode if safety_mode is not None else SafetyMode.NORMAL
        return self._mapper.plan(response, safety_mode=effective_mode, dry_run=dry_run)

    def validate(self, response: Any) -> Dict[str, Any]:
        return self._mapper.validate(response)

    def capabilities(self, safety_mode: Any = None) -> Any:
        effective_mode = safety_mode if safety_mode is not None else SafetyMode.NORMAL
        return self._mapper.capabilities(effective_mode)

    def snapshot(self) -> Dict[str, Any]:
        return self._mapper.snapshot()

    def healthcheck(self) -> PluginHealthCheck:
        snap = self._mapper.snapshot()
        return PluginHealthCheck(
            plugin_id=self.plugin_id,
            status=PluginHealthStatus.HEALTHY,
            summary=(
                f"{snap['routine_count']} routines, {snap['emote_count']} emotes, "
                f"{snap['accessory_count']} accessories — dry_run={snap['dry_run']}"
            ),
            details=snap,
        )


# ---------------------------------------------------------------------------
# RuleBasedSafetyGatePlugin
# ---------------------------------------------------------------------------

class RuleBasedSafetyGatePlugin(SafetyGatePlugin):
    """
    State-aware, per-routine-ID rate-limiting safety gate.

    Config keys (all optional):
        global_rate_limit_seconds (float):
            Minimum seconds between any two consecutive requests. Default: 0.5.
        routine_cooldowns (dict[str, float]):
            Per-routine-ID cooldown override in seconds.
            e.g. ``{"greet_guest": 20.0, "photo_pose": 30.0}``

    Example plugin config (YAML):
        plugins:
          sweetiebot.integration.safety_gate:
            global_rate_limit_seconds: 1.0
            routine_cooldowns:
              greet_guest: 20.0
              photo_pose: 30.0
    """

    plugin_id   = "sweetiebot.integration.safety_gate"
    plugin_type = PluginType.SAFETY_GATE
    priority    = 10

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._gate = SafetyGate(
            global_rate_limit=float(self.config.get("global_rate_limit_seconds", 0.5)),
            routine_cooldowns=self.config.get("routine_cooldowns"),
        )

    def configure(self, config: Dict[str, Any] | None = None) -> None:
        super().configure(config)
        if config:
            if "global_rate_limit_seconds" in config:
                self._gate._global_rate_limit = float(config["global_rate_limit_seconds"])
            if "routine_cooldowns" in config:
                self._gate._cooldowns.update(config["routine_cooldowns"])

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self.plugin_id,
            plugin_type=PluginType.SAFETY_GATE,
            version="0.1.1",
            display_name="Rule-Based Safety Gate",
            description=(
                "Fail-closed safety gate for the CERBERUS integration pipeline. "
                "Enforces per-routine cooldowns, NORMAL/SAFE/DEGRADED/EMERGENCY modes, "
                "and operator overrides. Maintains a bounded audit log."
            ),
            priority=self.priority,
            capabilities=["rate_limiting", "mode_aware", "operator_override", "audit_log"],
            built_in=True,
            config_schema={
                "global_rate_limit_seconds": {"type": "number", "default": 0.5},
                "routine_cooldowns": {"type": "object"},
            },
        )

    # ── SafetyGatePlugin interface ──────────────────────────────────────

    def check(self, response: Any, *, operator_override: bool = False) -> Any:
        return self._gate.check(response, operator_override=operator_override)

    def validate_only(self, response: Any) -> Any:
        return self._gate.validate_only(response)

    def set_safety_mode(self, mode: Any) -> None:
        self._gate.set_safety_mode(mode)

    def set_operator_override(self, active: bool) -> None:
        self._gate.set_operator_override(active)

    @property
    def safety_mode(self) -> Any:
        return self._gate.safety_mode

    def snapshot(self) -> Dict[str, Any]:
        return self._gate.snapshot()

    def recent_audit(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._gate.recent_audit(limit=limit)

    def healthcheck(self) -> PluginHealthCheck:
        snap = self._gate.snapshot()
        mode = snap["safety_mode"]
        status = (
            PluginHealthStatus.DEGRADED
            if mode in ("safe", "degraded", "emergency")
            else PluginHealthStatus.HEALTHY
        )
        return PluginHealthCheck(
            plugin_id=self.plugin_id,
            status=status,
            summary=f"safety_mode={mode} active_cooldowns={len(snap['active_cooldowns'])}",
            details=snap,
        )


# ---------------------------------------------------------------------------
# MemoryContextBuilderPlugin
# ---------------------------------------------------------------------------

class MemoryContextBuilderPlugin(MemoryContextPlugin):
    """
    Builds concise natural-language context from recent memory records.

    This feeds the memory→dialogue feedback loop: every ``/character/say``
    or ``/character/respond`` call pulls recent memory, runs it through this
    plugin, and injects the result so Sweetie-Bot avoids repeating herself.

    Config keys (all optional):
        max_context_chars (int):
            Hard character limit on the context string. Default: 400.
        max_records (int):
            Maximum number of memory records to consider. Default: 10.

    Example plugin config (YAML):
        plugins:
          sweetiebot.memory.context_builder:
            max_context_chars: 300
            max_records: 8
    """

    plugin_id   = "sweetiebot.memory.context_builder"
    plugin_type = PluginType.MEMORY_CONTEXT
    priority    = 10

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._max_chars   = int(self.config.get("max_context_chars", 400))
        self._max_records = int(self.config.get("max_records", 10))

    def configure(self, config: Dict[str, Any] | None = None) -> None:
        super().configure(config)
        if config:
            if "max_context_chars" in config:
                self._max_chars = int(config["max_context_chars"])
            if "max_records" in config:
                self._max_records = int(config["max_records"])

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self.plugin_id,
            plugin_type=PluginType.MEMORY_CONTEXT,
            version="0.1.1",
            display_name="Memory Context Builder",
            description=(
                "Condenses recent memory records into a natural-language context string "
                "for injection into dialogue generation, enabling the memory→dialogue "
                "feedback loop. Also extracts recently used routine/emote IDs so the "
                "behavior director can avoid repetition."
            ),
            priority=self.priority,
            capabilities=["context_summary", "recent_commands"],
            built_in=True,
            config_schema={
                "max_context_chars": {"type": "integer", "default": 400},
                "max_records":       {"type": "integer", "default": 10},
            },
        )

    # ── MemoryContextPlugin interface ───────────────────────────────────

    def build_context_summary(
        self,
        records: List[Dict[str, Any]],
        *,
        current_mood: str = "calm",
        current_routine: Optional[str] = None,
        max_chars: int = 0,
    ) -> str:
        return build_context_summary(
            records[: self._max_records],
            current_mood=current_mood,
            current_routine=current_routine,
            max_chars=max_chars or self._max_chars,
        )

    def extract_recent_commands(
        self,
        records: List[Dict[str, Any]],
        *,
        limit: int = 5,
    ) -> Dict[str, List[str]]:
        return extract_recent_commands(records, limit=limit)

    def healthcheck(self) -> PluginHealthCheck:
        return PluginHealthCheck(
            plugin_id=self.plugin_id,
            status=PluginHealthStatus.HEALTHY,
            summary=f"max_chars={self._max_chars} max_records={self._max_records}",
            details={"max_context_chars": self._max_chars, "max_records": self._max_records},
        )

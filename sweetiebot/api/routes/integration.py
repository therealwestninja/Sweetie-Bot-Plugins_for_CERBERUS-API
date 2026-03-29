"""
sweetiebot.api.routes.integration
===================================
FastAPI routes for the Sweetie-Bot ↔ CERBERUS integration layer.

Endpoints
---------
POST /integration/plan
    Takes a CharacterResponse, runs it through the safety gate and mapper,
    returns an IntegrationPlan. Does NOT execute anything on CERBERUS.

POST /integration/validate
    Dry-run validation only. Returns a ValidationResult.
    Does not mutate any state (no cooldowns consumed, no audit entries).

GET /integration/capabilities
    Returns the current CapabilityManifest: what routines / emotes /
    accessories Sweetie-Bot may currently request.

POST /integration/safety/mode
    Operator endpoint: change the gate's safety mode.

POST /integration/safety/override
    Operator endpoint: toggle the operator override flag.

GET /debug/last-decision
    Returns the last N decisions recorded in the DecisionLedger.
    Intended for developer debugging; should be protected in production.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sweetiebot.integration.cerberus_mapper import CerberusMapper
from sweetiebot.integration.schemas import (
    CharacterResponse,
    IntegrationPlan,
    SafetyMode,
    ValidationResult,
    WSEvent,
    WSEventType,
)
from sweetiebot.observability.structured_log import get_ledger
from sweetiebot.safety.gate import SafetyGate

router = APIRouter(prefix="/integration", tags=["integration"])
debug_router = APIRouter(prefix="/debug", tags=["debug"])


# ---------------------------------------------------------------------------
# Request / Response helpers
# ---------------------------------------------------------------------------

class SafetyModeRequest(BaseModel):
    mode: SafetyMode
    reason: Optional[str] = None
    operator_id: str = "operator"


class OverrideRequest(BaseModel):
    active: bool
    operator_id: str = "operator"
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Dependency: get the mapper and gate from app state
# ---------------------------------------------------------------------------

def _get_mapper(request: Any = None) -> CerberusMapper:
    """Pulled from app.state by the route; injected via closure in create_integration_router."""
    raise NotImplementedError("Use create_integration_router()")


def _get_gate(request: Any = None) -> SafetyGate:
    raise NotImplementedError("Use create_integration_router()")


# ---------------------------------------------------------------------------
# Router factory — wires real instances from app.state
# ---------------------------------------------------------------------------

def create_integration_router(
    mapper: CerberusMapper,
    gate: SafetyGate,
) -> APIRouter:
    """
    Build and return the integration APIRouter with real mapper/gate instances
    bound via closures (no global state).
    """
    router = APIRouter(prefix="/integration", tags=["integration"])
    debug_router_inner = APIRouter(prefix="/debug", tags=["debug"])
    ledger = get_ledger()

    # ── POST /integration/plan ─────────────────────────────────────────────
    @router.post("/plan", response_model=Dict[str, Any])
    def plan(
        response: CharacterResponse,
        operator_override: bool = False,
    ) -> Dict[str, Any]:
        """
        Convert a CharacterResponse into a CERBERUS IntegrationPlan.

        The plan is never executed here — CERBERUS consumes it.
        Returns the plan regardless of approval status so the caller
        can inspect rejection reasons.
        """
        t_start = time.perf_counter()

        # 1. Safety gate check
        gate_result = gate.check(response, operator_override=operator_override)

        # 2. If gate blocks, return a rejected plan without going to the mapper
        if not gate_result.allowed:
            from sweetiebot.integration.schemas import PlanRejectionReason
            plan_obj = IntegrationPlan(
                source_response_id=response.response_id,
                approved=False,
                commands=[],
                dry_run=mapper.dry_run,
                rejection_reasons=gate_result.rejection_reasons,
                rejection_detail=gate_result.rejection_detail,
                safety_mode_at_planning=gate_result.safety_mode,
            )
            elapsed = round((time.perf_counter() - t_start) * 1000, 2)
            ledger.record("integration.plan.rejected", {
                "plan_id": plan_obj.plan_id,
                "response_id": response.response_id,
                "reasons": [r.value for r in gate_result.rejection_reasons],
                "detail": gate_result.rejection_detail,
                "gate_mode": gate_result.safety_mode.value,
            }, elapsed_ms=elapsed)
            return {**plan_obj.model_dump(), "elapsed_ms": elapsed, "_gate": gate_result.to_dict()}

        # 3. Mapper translates to CERBERUS commands
        plan_obj = mapper.plan(response, safety_mode=gate_result.safety_mode)

        elapsed = round((time.perf_counter() - t_start) * 1000, 2)
        decision_type = "integration.plan.created" if plan_obj.approved else "integration.plan.rejected"
        ledger.record(decision_type, {
            "plan_id": plan_obj.plan_id,
            "response_id": response.response_id,
            "approved": plan_obj.approved,
            "command_count": len(plan_obj.commands),
            "commands": [
                {"type": c.command_type.value, "id": c.command_id}
                for c in plan_obj.commands
            ],
            "dry_run": plan_obj.dry_run,
            "rejection_reasons": [r.value for r in plan_obj.rejection_reasons],
            "safety_mode": plan_obj.safety_mode_at_planning.value,
        }, elapsed_ms=elapsed)

        return {**plan_obj.model_dump(), "elapsed_ms": elapsed}

    # ── POST /integration/validate ─────────────────────────────────────────
    @router.post("/validate", response_model=Dict[str, Any])
    def validate(response: CharacterResponse) -> Dict[str, Any]:
        """
        Validate a CharacterResponse without mutating any state.

        Runs both the safety gate (read-only) and the mapper's own
        validator. Useful for pre-flight checks from the Web UI.
        """
        t_start = time.perf_counter()

        gate_validation = gate.validate_only(response)
        mapper_validation = mapper.validate(response)

        # Merge issues and warnings
        all_issues = gate_validation.issues + mapper_validation["issues"]
        all_warnings = gate_validation.warnings + mapper_validation["warnings"]

        result = ValidationResult(
            valid=len(all_issues) == 0,
            issues=all_issues,
            warnings=all_warnings,
            safety_mode=gate_validation.safety_mode,
            would_approve=len(all_issues) == 0 and gate_validation.would_approve,
        )

        elapsed = round((time.perf_counter() - t_start) * 1000, 2)
        ledger.record("integration.validate", {
            "response_id": response.response_id,
            "valid": result.valid,
            "issue_count": len(all_issues),
            "warning_count": len(all_warnings),
        }, elapsed_ms=elapsed)

        return {**result.model_dump(), "elapsed_ms": elapsed}

    # ── GET /integration/capabilities ──────────────────────────────────────
    @router.get("/capabilities", response_model=Dict[str, Any])
    def capabilities() -> Dict[str, Any]:
        """
        Return the current CapabilityManifest.

        Lists all allowlisted routines, emotes, and accessories.
        The list may be filtered based on the current safety mode.
        """
        manifest = mapper.capabilities(safety_mode=gate.safety_mode)
        return manifest.model_dump()

    # ── POST /integration/safety/mode ──────────────────────────────────────
    @router.post("/safety/mode", response_model=Dict[str, Any])
    def set_safety_mode(request: SafetyModeRequest) -> Dict[str, Any]:
        """
        Operator endpoint: change the safety gate's operating mode.
        This is a privileged operation — protect it in production.
        """
        prev_mode = gate.safety_mode
        gate.set_safety_mode(request.mode)

        ledger.record("safety.mode.changed", {
            "prev_mode": prev_mode.value,
            "new_mode": request.mode.value,
            "operator_id": request.operator_id,
            "reason": request.reason,
        })

        return {
            "ok": True,
            "prev_mode": prev_mode.value,
            "new_mode": request.mode.value,
            "operator_id": request.operator_id,
            "gate": gate.snapshot(),
        }

    # ── POST /integration/safety/override ──────────────────────────────────
    @router.post("/safety/override", response_model=Dict[str, Any])
    def set_override(request: OverrideRequest) -> Dict[str, Any]:
        """
        Operator endpoint: enable or disable the operator override flag.
        When active, rate limits are bypassed for the next request.
        """
        gate.set_operator_override(request.active)

        ledger.record("operator.override", {
            "active": request.active,
            "operator_id": request.operator_id,
            "reason": request.reason,
        })

        return {
            "ok": True,
            "operator_override_active": request.active,
            "gate": gate.snapshot(),
        }

    # ── GET /integration/gate ──────────────────────────────────────────────
    @router.get("/gate", response_model=Dict[str, Any])
    def gate_status() -> Dict[str, Any]:
        """Current state of the safety gate."""
        return {
            "gate": gate.snapshot(),
            "recent_audit": gate.recent_audit(limit=10),
        }

    # ── GET /integration/mapper ────────────────────────────────────────────
    @router.get("/mapper", response_model=Dict[str, Any])
    def mapper_status() -> Dict[str, Any]:
        """Current state of the CERBERUS mapper (allowlists, dry_run mode)."""
        return mapper.snapshot()

    # ── GET /debug/last-decision ───────────────────────────────────────────
    @debug_router_inner.get("/last-decision", response_model=Dict[str, Any])
    def last_decision(limit: int = 5) -> Dict[str, Any]:
        """
        Returns the last N decisions recorded by the integration layer.

        Includes plan creation/rejection, validation results, safety mode
        changes, and operator events. Intended for developer debugging.
        """
        return {
            "ledger": ledger.snapshot(),
            "recent_decisions": ledger.recent(limit=min(limit, 50)),
        }

    @debug_router_inner.get("/decisions/{decision_type}", response_model=Dict[str, Any])
    def decisions_by_type(decision_type: str, limit: int = 10) -> Dict[str, Any]:
        """Filter the decision ledger by decision type."""
        return {
            "decision_type": decision_type,
            "decisions": ledger.by_type(decision_type, limit=min(limit, 50)),
        }

    # Return a combined router (FastAPI doesn't support sub-router nesting
    # directly in all versions, so we return both separately)
    return router, debug_router_inner

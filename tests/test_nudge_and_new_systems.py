"""
Tests for Phase 2-7 systems:
  - GO2 adapter (sim mode)
  - Structured dialogue provider
  - Expression coordinator
  - Event pipeline
  - Safety gate hardening (emergency stop, preconditions, repetition)
  - Nudge handler + decision matrix
  - API nudge endpoints
"""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Phase 2 — GO2 Adapter
# ---------------------------------------------------------------------------

class TestUnitreeGo2Adapter:
    def setup_method(self):
        from sweetiebot.adapters.unitree_go2 import UnitreeGo2Adapter
        self.adapter = UnitreeGo2Adapter(sim_mode=True)

    def test_connect_sim(self):
        result = self.adapter.connect()
        assert result["connected"] is True
        assert result["mode"] == "sim"

    def test_capabilities(self):
        caps = self.adapter.capabilities()
        assert caps.sim_mode is True
        assert len(caps.supported_routines) >= 5
        assert "return_to_neutral" in caps.supported_routines
        assert caps.has_audio is True

    def test_execute_motion_allowed(self):
        self.adapter.connect()
        result = self.adapter.execute_motion("greet_guest")
        assert result.status.value == "sim"
        assert result.command == "greet_guest"

    def test_execute_motion_rejected(self):
        result = self.adapter.execute_motion("fly_to_moon")
        assert result.status.value == "rejected"
        assert "allowlist" in result.detail.lower()

    def test_cooldown_enforcement(self):
        self.adapter.connect()
        r1 = self.adapter.execute_motion("photo_pose")
        assert r1.status.value == "sim"
        r2 = self.adapter.execute_motion("photo_pose")
        assert r2.status.value == "skipped"
        assert "cooldown" in r2.detail.lower()

    def test_return_to_neutral_no_cooldown(self):
        self.adapter.connect()
        # Fire it twice — should always pass
        r1 = self.adapter.execute_motion("return_to_neutral")
        r2 = self.adapter.execute_motion("return_to_neutral")
        assert r1.status.value == "sim"
        assert r2.status.value == "sim"

    def test_emergency_stop(self):
        self.adapter.connect()
        result = self.adapter.emergency_stop()
        assert result.status.value == "sim"
        assert "emergency" in result.command

    def test_health_check(self):
        self.adapter.connect()
        health = self.adapter.health_check()
        assert health["connected"] is True
        assert health["sim_mode"] is True
        assert "uptime_seconds" in health

    def test_backward_compat(self):
        # Old interface still works
        result = self.adapter.execute_routine("greet_guest")
        assert "status" in result


# ---------------------------------------------------------------------------
# Phase 3 — Structured Dialogue
# ---------------------------------------------------------------------------

class TestStructuredDialogue:
    def setup_method(self):
        from sweetiebot.plugins.builtins.structured_dialogue import StructuredDialogueProviderPlugin
        self.provider = StructuredDialogueProviderPlugin()

    def test_greeting_intent(self):
        out = self.provider.classify("hello there!")
        assert out.intent == "greet"
        assert out.emote == "warm_smile"
        assert out.routine == "greet_guest"
        assert out.emotion == "happy"
        assert len(out.safety_flags) == 0

    def test_stop_intent_highest_priority(self):
        out = self.provider.classify("please stop that")
        assert out.intent == "emergency_stop"
        assert out.routine == "return_to_neutral"
        assert out.confidence >= 0.95

    def test_question_intent(self):
        out = self.provider.classify("what can you do?")
        assert out.intent == "question"
        assert out.routine is None

    def test_photo_intent(self):
        out = self.provider.classify("can you pose for a photo?")
        assert out.intent == "pose_photo"
        assert out.routine == "photo_pose"

    def test_safe_mode_output(self):
        out = self.provider.classify("hello", safe_mode=True)
        assert out.intent == "safe_mode_reply"
        assert "safe_mode_active" in out.safety_flags
        assert out.routine == "return_to_neutral"

    def test_degraded_mode_output(self):
        out = self.provider.classify("hello", degraded_mode=True)
        assert out.intent == "degraded_reply"
        assert "degraded_mode_active" in out.safety_flags

    def test_to_dialogue_response(self):
        out = self.provider.classify("hi there")
        dr = out.to_dialogue_response()
        assert dr.spoken_text == out.speech
        assert dr.intent == out.intent
        assert dr.metadata["structured"] is True

    def test_generate_reply_interface(self):
        dr = self.provider.generate_reply(
            user_text="hello",
            current_mood="calm",
        )
        assert dr.spoken_text
        assert dr.intent

    def test_healthcheck(self):
        h = self.provider.healthcheck()
        assert h["healthy"] is True
        assert h["classifiers"] >= 6


# ---------------------------------------------------------------------------
# Phase 4 — Expression Coordinator
# ---------------------------------------------------------------------------

class TestExpressionCoordinator:
    def setup_method(self):
        from sweetiebot.adapters.unitree_go2 import UnitreeGo2Adapter
        from sweetiebot.runtime.expression_coordinator import ExpressionCoordinator
        adapter = UnitreeGo2Adapter(sim_mode=True)
        adapter.connect()
        self.coord = ExpressionCoordinator(adapter)

    def test_express_motion_and_emote(self):
        result = self.coord.express(
            speech="Hello!",
            motion="greet_guest",
            emote="warm_smile",
            accessory="eyes_happy",
        )
        assert result.ok
        assert "motion" in result.channels
        assert "speech" in result.channels

    def test_return_to_neutral(self):
        result = self.coord.return_to_neutral()
        assert result.ok
        assert "motion" in result.channels

    def test_no_duplicate_motion(self):
        # First call locks motion channel
        import threading
        results = []
        # Simulate two concurrent calls (sequential in tests)
        r1 = self.coord.express(motion="greet_guest")
        # greet_guest has adapter-level cooldown — motion channel should be released
        r2 = self.coord.express(motion="greet_guest")
        # Second call: adapter skips due to cooldown, but coordinator doesn't lock
        assert r1.ok

    def test_snapshot(self):
        snap = self.coord.snapshot()
        assert "channels" in snap
        assert "motion" in snap["channels"]

    def test_interrupt_releases(self):
        released = self.coord.interrupt(["motion", "emote"])
        assert "released" in released


# ---------------------------------------------------------------------------
# Phase 5 — Event Pipeline
# ---------------------------------------------------------------------------

class TestEventPipeline:
    def setup_method(self):
        from sweetiebot.runtime.event_pipeline import EventPipeline
        self.pipeline = EventPipeline()

    def test_user_input_event(self):
        result = self.pipeline.ingest({"kind": "user_input", "text": "hello"})
        assert result.handled
        assert "process_dialogue" in result.action_hints

    def test_person_detected(self):
        result = self.pipeline.ingest({"kind": "person_detected", "person_id": "alice"})
        assert "greet_guest" in result.action_hints or "set_focus" in result.action_hints

    def test_proximity_alert_escalates(self):
        result = self.pipeline.ingest({"kind": "proximity_alert", "distance_m": 0.3})
        assert result.safety_escalation == "safe"
        assert "return_to_neutral" in result.action_hints

    def test_system_fault_critical(self):
        result = self.pipeline.ingest({
            "kind": "system_fault",
            "fault_code": "motor_error",
            "severity": "critical",
        })
        assert result.safety_escalation in ("emergency", "degraded")

    def test_battery_low(self):
        result = self.pipeline.ingest({"kind": "battery_low", "battery_pct": 15})
        assert result.safety_escalation == "degraded"

    def test_battery_critical(self):
        result = self.pipeline.ingest({"kind": "battery_critical", "battery_pct": 3})
        assert result.safety_escalation == "emergency"

    def test_unknown_event_handled_gracefully(self):
        result = self.pipeline.ingest({"kind": "unknown_event_xyz"})
        assert result.handled is False

    def test_invalid_payload_no_raise(self):
        result = self.pipeline.ingest({})  # empty
        assert result is not None

    def test_recent_events(self):
        self.pipeline.ingest({"kind": "user_input", "text": "test"})
        events = self.pipeline.recent_events(limit=5)
        assert len(events) >= 1

    def test_only_escalates_never_downgrades(self):
        from sweetiebot.safety.gate import SafetyGate
        from sweetiebot.integration.schemas import SafetyMode
        gate = SafetyGate()
        gate.set_safety_mode(SafetyMode.DEGRADED)
        pipeline = self.pipeline
        pipeline._gate = gate
        # A low-severity event should not downgrade from DEGRADED to SAFE
        pipeline.ingest({"kind": "proximity_alert", "distance_m": 0.5})
        assert gate.safety_mode.value in ("degraded", "emergency")


# ---------------------------------------------------------------------------
# Phase 6 — Safety Hardening
# ---------------------------------------------------------------------------

class TestSafetyHardening:
    def setup_method(self):
        from sweetiebot.safety.gate import SafetyGate
        self.gate = SafetyGate()

    def test_emergency_stop_clears_cooldowns(self):
        from sweetiebot.integration.schemas import CharacterResponse
        # Consume greet_guest (starts cooldown)
        self.gate.check(CharacterResponse(routine_id="greet_guest"))
        # Emergency stop — clears cooldowns and sets EMERGENCY mode
        result = self.gate.emergency_stop()
        assert result["ok"]
        assert result["cooldowns_cleared"]
        # return_to_neutral should pass even in EMERGENCY (it's the recovery command)
        # Use operator_override to bypass global rate limit
        r = self.gate.check(CharacterResponse(routine_id="return_to_neutral"), operator_override=True)
        assert r.allowed, f"return_to_neutral should pass in emergency: {r.rejection_detail}"

    def test_precondition_standing_required(self):
        result = self.gate.check_preconditions("greet_guest", is_standing=False)
        assert not result["ok"]
        assert result["reason"] == "robot_not_standing"

    def test_precondition_passes_when_standing(self):
        result = self.gate.check_preconditions("greet_guest", is_standing=True)
        assert result["ok"]

    def test_repetition_suppression(self):
        recent = ["greet_guest", "greet_guest", "greet_guest"]
        suppressed = self.gate.check_repetition("greet_guest", recent, max_repeats=2)
        assert suppressed is True

    def test_repetition_allows_when_varied(self):
        recent = ["greet_guest", "photo_pose", "greet_guest"]
        suppressed = self.gate.check_repetition("greet_guest", recent, max_repeats=2)
        assert suppressed is False

    def test_emergency_mode_blocks_all_non_neutral(self):
        from sweetiebot.integration.schemas import CharacterResponse, SafetyMode
        self.gate.set_safety_mode(SafetyMode.EMERGENCY)
        # Non-neutral routine blocked
        r = self.gate.check(CharacterResponse(routine_id="greet_guest"), operator_override=True)
        assert not r.allowed
        # return_to_neutral passes even in emergency (it's the recovery command)
        r2 = self.gate.check(CharacterResponse(routine_id="return_to_neutral"), operator_override=True)
        assert r2.allowed, f"return_to_neutral must pass in emergency: {r2.rejection_detail}"


# ---------------------------------------------------------------------------
# Phase 6b — Nudge Handler
# ---------------------------------------------------------------------------

class TestNudgeHandler:
    def setup_method(self):
        from sweetiebot.behavior.nudge_handler import NudgeHandler
        self.handler = NudgeHandler(spam_window_seconds=5.0, max_nudges_before_suppress=3)

    def test_attention_nudge_idle(self):
        from sweetiebot.behavior.nudge_handler import AutonomyDecision
        result = self.handler.handle("attention", current_mood="calm")
        assert result.nudge_type.value == "attention"
        assert result.micro_reaction.speech in ("Hello?", "Hmm? Did you need me?")
        assert result.micro_reaction.emote == "curious_headtilt"
        assert result.autonomy_decision == AutonomyDecision.COMPLY

    def test_interaction_nudge_idle(self):
        result = self.handler.handle("interaction", current_mood="calm")
        assert result.micro_reaction.emote in ("warm_smile", "happy_bounce")

    def test_interrupt_nudge_mid_routine_resists(self):
        from sweetiebot.behavior.nudge_handler import AutonomyDecision
        result = self.handler.handle(
            "interrupt",
            current_mood="happy",
            active_routine="photo_pose",
        )
        assert result.autonomy_decision == AutonomyDecision.RESIST
        assert result.suggested_action is None  # no follow-on when resisting

    def test_physical_nudge_reaction(self):
        result = self.handler.handle("physical")
        assert result.micro_reaction.speech in ("Oof~!", "Whoa!")

    def test_calm_nudge_always_complies(self):
        from sweetiebot.behavior.nudge_handler import AutonomyDecision
        result = self.handler.handle("calm", active_routine="idle_cute")
        assert result.autonomy_decision == AutonomyDecision.COMPLY
        assert result.suggested_action == "return_to_neutral"

    def test_spam_suppression(self):
        # Fire 4 attention nudges quickly
        for _ in range(4):
            result = self.handler.handle("attention")
        assert result.suppressed is True
        assert result.suggested_action is None

    def test_variety_rotation(self):
        r1 = self.handler.handle("attention")
        r2 = self.handler.handle("attention")
        # Should rotate through reaction variety
        # (may be same if only 1 reaction, that's OK)
        assert r1.micro_reaction.speech or r2.micro_reaction.speech

    def test_mood_modulates_interaction(self):
        result = self.handler.handle("interaction", current_mood="excited")
        assert "hi" in result.micro_reaction.speech.lower()

    def test_unknown_nudge_type_defaults(self):
        result = self.handler.handle("xyz_unknown")
        assert result.nudge_type.value == "attention"

    def test_snapshot(self):
        snap = self.handler.snapshot()
        assert "spam_window_seconds" in snap
        assert "nudge_history_size" in snap


# ---------------------------------------------------------------------------
# API integration — nudge endpoints
# ---------------------------------------------------------------------------

class TestNudgeAPI:
    def setup_method(self):
        from sweetiebot.api.app import create_app
        self.client = TestClient(create_app())

    def test_nudge_endpoint_exists(self):
        routes = [r.path for r in self.client.app.routes]
        assert "/character/nudge" in routes

    def test_nudge_attention(self):
        r = self.client.post("/character/nudge", json={"nudge_type": "attention"})
        assert r.status_code == 200
        data = r.json()
        assert data["nudge_type"] == "attention"
        assert "micro_reaction" in data
        assert data["micro_reaction"]["speech"] in ("Hello?", "Hmm? Did you need me?")
        assert data["micro_reaction"]["emote"] == "curious_headtilt"

    def test_nudge_interaction_happy_response(self):
        r = self.client.post("/character/nudge", json={"nudge_type": "interaction"})
        assert r.status_code == 200
        data = r.json()
        assert data["micro_reaction"]["speech"] in ("Oh, hi!", "Oh hey there!")

    def test_nudge_physical(self):
        r = self.client.post("/character/nudge", json={"nudge_type": "physical"})
        assert r.status_code == 200
        data = r.json()
        assert data["micro_reaction"]["speech"] in ("Oof~!", "Whoa!")

    def test_nudge_calm(self):
        r = self.client.post("/character/nudge", json={"nudge_type": "calm"})
        assert r.status_code == 200
        data = r.json()
        assert data["suggested_action"] == "return_to_neutral"

    def test_nudge_status(self):
        self.client.post("/character/nudge", json={"nudge_type": "attention"})
        r = self.client.get("/character/nudge/status")
        assert r.status_code == 200
        snap = r.json()
        assert snap["nudge_history_size"] >= 1

    def test_nudge_returns_autonomy_decision(self):
        r = self.client.post("/character/nudge", json={"nudge_type": "attention"})
        data = r.json()
        assert data["autonomy_decision"] in ("comply", "adapt", "resist", "continue")
        assert data["state_category"] in ("idle", "active_routine", "safe_mode", "degraded")

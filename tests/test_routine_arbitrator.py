from sweetiebot.routines.arbitrator import RoutineArbitrator
from sweetiebot.runtime import SweetieBotRuntime


def test_routine_arbitrator_allows_basic_routine():
    arb = RoutineArbitrator()
    result = arb.arbitrate(
        requested_routine="greet_guest",
        active_routine=None,
    )
    assert result["allowed"] is True
    assert result["routine_id"] == "greet_guest"


def test_routine_arbitrator_blocks_cooldown():
    arb = RoutineArbitrator()
    first = arb.arbitrate(requested_routine="photo_pose", active_routine=None)
    second = arb.arbitrate(requested_routine="photo_pose", active_routine=None)
    assert first["allowed"] is True
    assert second["allowed"] is False
    assert second["reason"] == "routine_on_cooldown"


def test_runtime_behavior_arbitration():
    runtime = SweetieBotRuntime()
    result = runtime.suggest_and_arbitrate_behavior("hello there")
    assert result["behavior"]["routine_id"] == "greet_guest"
    assert result["routine_arbitration"]["allowed"] is True

from sweetiebot.runtime import SweetieBotRuntime


def test_runtime_bootstraps_builtin_routines() -> None:
    runtime = SweetieBotRuntime()
    result = runtime.handle_text("hello")
    assert result["reply"]["directive"]["routine_id"] == "greet_guest"
    assert result["state"]["current_routine_id"] == "greet_guest"
    assert result["state"]["degraded_mode"] is False


def test_runtime_strips_unknown_routine_and_enters_degraded_mode() -> None:
    runtime = SweetieBotRuntime()
    runtime.routines._routines.pop("photo_pose", None)  # type: ignore[attr-defined]
    result = runtime.handle_text("camera pose please")
    assert result["reply"]["directive"]["routine_id"] is None
    assert result["state"]["degraded_mode"] is True


def test_runtime_stop_sets_safe_mode() -> None:
    runtime = SweetieBotRuntime()
    state = runtime.apply_operator_stop()
    assert state.safe_mode is True
    assert state.current_routine_id == "return_to_neutral"

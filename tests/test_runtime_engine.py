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


def test_runtime_can_configure_safety_plugin_and_clip_reply() -> None:
    runtime = SweetieBotRuntime()
    runtime.configure_plugins(
        {"sweetiebot.default_safety_policy": {"max_spoken_chars": 20}}
    )
    result = runtime.handle_text("hello")
    assert len(result["reply"]["text"]) <= 21
    assert result["reply"]["fallback_mode"] is True


def test_runtime_safety_policy_can_force_neutral_cancel() -> None:
    runtime = SweetieBotRuntime()
    runtime.configure_plugins(
        {"sweetiebot.default_safety_policy": {"blocked_terms": ["sparkle"]}}
    )
    runtime.configure_persona(
        {
            "id": "sweetiebot_convention",
            "preferred_greeting": "Sparkle sparkle sparkle forever.",
        }
    )
    result = runtime.handle_text("hello")
    assert result["reply"]["intent"] == "cancel"
    assert result["reply"]["directive"]["routine_id"] == "return_to_neutral"
    assert result["state"]["safe_mode"] is True

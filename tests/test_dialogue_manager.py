from sweetiebot.dialogue.manager import DialogueManager


def test_dialogue_manager_returns_structured_reply() -> None:
    dm = DialogueManager()
    reply = dm.reply_for("hello")
    assert reply.text
    assert reply.directive.emote_id == "curious_headtilt"
    assert reply.directive.routine_id == "greet_guest"


def test_dialogue_manager_changes_with_persona() -> None:
    dm = DialogueManager()
    dm.configure_persona(
        {
            "id": "sweetiebot_convention",
            "dialogue_style": {"tone": "bright"},
            "preferred_greeting": "Hi everypony! Sparkle stations are ready.",
            "defaults": {"emote": "happy_bounce", "accessory_scene": "eyes_showtime"},
        }
    )
    reply = dm.reply_for("hello")
    assert "sparkle" in reply.text.lower()
    assert reply.directive.accessory_scene_id == "eyes_showtime"
    assert reply.directive.emote_id == "happy_bounce"


def test_dialogue_manager_cancel_path_is_safe() -> None:
    dm = DialogueManager()
    reply = dm.reply_for("stop please")
    assert reply.intent.value == "cancel"
    assert reply.directive.routine_id == "return_to_neutral"
    assert "neutral" in reply.text.lower()

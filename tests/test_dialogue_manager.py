from sweetiebot.dialogue.manager import DialogueManager


def test_dialogue_manager_returns_reply() -> None:
    dm = DialogueManager()
    reply = dm.reply_for("hello")
    assert reply.text


def test_dialogue_manager_changes_with_persona() -> None:
    dm = DialogueManager()
    dm.configure_persona({"id": "sweetiebot_convention", "dialogue_style": {"tone": "bright"}})
    reply = dm.reply_for("hello")
    assert "sparkle" in reply.text.lower()

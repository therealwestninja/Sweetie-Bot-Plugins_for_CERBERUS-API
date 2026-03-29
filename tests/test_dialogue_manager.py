from sweetiebot.dialogue.manager import DialogueManager


def test_dialogue_manager_returns_reply():
    dm = DialogueManager()
    reply = dm.reply_for("hello")
    assert reply.text

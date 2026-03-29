from sweetiebot.plugins.builtins.dialogue import RuleBasedDialogueProviderPlugin
from sweetiebot.runtime import SweetieBotRuntime


def test_rule_based_dialogue_greeting():
    plugin = RuleBasedDialogueProviderPlugin()
    reply = plugin.generate_reply(
        user_text="hello there",
        current_mood="calm",
        current_focus="guest",
        active_routine=None,
    )
    assert reply.intent == "greet"
    assert reply.routine_id == "greet_guest"


def test_rule_based_dialogue_question():
    plugin = RuleBasedDialogueProviderPlugin()
    reply = plugin.generate_reply(
        user_text="what are you doing?",
        current_mood="curious",
        current_focus="guest",
        active_routine=None,
    )
    assert reply.intent == "question_reply"
    assert reply.emote_id == "curious_tilt"


def test_runtime_generate_dialogue_updates_state():
    runtime = SweetieBotRuntime()
    result = runtime.generate_dialogue("hello sweetie bot")
    assert result["intent"] == "greet"
    assert runtime.state["last_reply"] == "Hi there!"
    assert runtime.dialogue_status()["last_dialogue"] is not None

from sweetiebot.plugins.builtins.attention import RuleBasedAttentionStrategyPlugin
from sweetiebot.runtime import SweetieBotRuntime


def test_attention_strategy_guest_focus_from_text():
    strategy = RuleBasedAttentionStrategyPlugin()
    result = strategy.suggest_attention(
        user_text="hello sweetie bot",
        current_focus=None,
        current_mood="calm",
    )
    assert result.target == "guest"


def test_attention_strategy_operator_in_safe_mode():
    strategy = RuleBasedAttentionStrategyPlugin()
    result = strategy.suggest_attention(
        user_text="look here",
        current_focus="guest",
        current_mood="happy",
        safe_mode=True,
    )
    assert result.target == "operator"


def test_runtime_apply_attention_updates_focus():
    runtime = SweetieBotRuntime()
    result = runtime.apply_attention(user_text="can you look here for a photo?")
    assert result["suggestion"]["target"] == "camera"
    assert result["state"]["focus_target"] == "camera"

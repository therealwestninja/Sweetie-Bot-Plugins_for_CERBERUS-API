from sweetiebot.behavior.director import BehaviorDirector
from sweetiebot.runtime import SweetieBotRuntime


def test_behavior_director_greeting():
    director = BehaviorDirector()
    result = director.suggest(
        user_text="hello sweetie bot",
        current_mood="calm",
        focus_target=None,
        active_routine=None,
    )
    assert result["action"] == "routine"
    assert result["routine_id"] == "greet_guest"


def test_behavior_director_photo_request():
    director = BehaviorDirector()
    result = director.suggest(
        user_text="can you pose for a photo?",
        current_mood="happy",
        focus_target=None,
        active_routine=None,
    )
    assert result["routine_id"] == "photo_pose"


def test_runtime_behavior_suggestion():
    runtime = SweetieBotRuntime()
    runtime.update_character_state(mood="curious")
    result = runtime.suggest_behavior("What are you doing?")
    assert result["action"] == "reply"
    assert result["emote_id"] in {"curious_tilt", "warm_smile"}

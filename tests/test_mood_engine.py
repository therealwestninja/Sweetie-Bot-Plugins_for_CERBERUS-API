from sweetiebot.mood.engine import MoodEngine
from sweetiebot.runtime import SweetieBotRuntime


def test_mood_engine_event_mapping():
    engine = MoodEngine()
    assert engine.apply_event("calm", "greet") == "warm"
    assert engine.apply_event("calm", "play") == "excited"


def test_mood_engine_decay():
    engine = MoodEngine()
    assert engine.decay("excited") == "happy"
    assert engine.decay("happy") == "warm"


def test_runtime_note_turn_infers_mood():
    runtime = SweetieBotRuntime()
    runtime.note_turn("Hello there!", "Hi!")
    assert runtime.character_state()["mood"] == "warm"


def test_runtime_apply_mood_event():
    runtime = SweetieBotRuntime()
    runtime.apply_mood_event("question")
    assert runtime.character_state()["mood"] == "curious"

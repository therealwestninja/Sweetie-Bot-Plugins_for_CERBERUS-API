from sweetiebot.plugins.builtins.emotes import RuleBasedEmoteMapperPlugin
from sweetiebot.runtime import SweetieBotRuntime


def test_emote_mapper_greeting():
    mapper = RuleBasedEmoteMapperPlugin()
    selection = mapper.map_emote(
        current_mood="warm",
        dialogue_intent="greet",
    )
    assert selection.emote_id == "warm_smile"


def test_emote_mapper_mood_mapping():
    mapper = RuleBasedEmoteMapperPlugin()
    selection = mapper.map_emote(
        current_mood="curious",
    )
    assert selection.emote_id == "curious_tilt"


def test_runtime_dialogue_maps_emote():
    runtime = SweetieBotRuntime()
    result = runtime.generate_dialogue("hello there")
    assert result["intent"] == "greet"
    emote = runtime.emote_status()
    assert emote["current_emote"] == "warm_smile"
    assert emote["last_emote"] is not None

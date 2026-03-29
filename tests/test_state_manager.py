from sweetiebot.plugins.builtins.memory import InMemoryStorePlugin
from sweetiebot.state.manager import CharacterStateManager
from sweetiebot.runtime import SweetieBotRuntime


def test_state_manager_updates_and_snapshot():
    memory = InMemoryStorePlugin()
    manager = CharacterStateManager(memory_store=memory)
    manager.set_mood("happy")
    manager.set_focus("operator")
    snap = manager.snapshot()
    assert snap["mood"] == "happy"
    assert snap["focus_target"] == "operator"


def test_state_manager_writes_memory_events():
    memory = InMemoryStorePlugin()
    manager = CharacterStateManager(memory_store=memory)
    manager.set_emote("excited_smile")
    results = memory.recent(limit=5)
    assert results
    assert results[0].kind in {"emote_change", "state_update"}


def test_runtime_note_turn_updates_character_state():
    runtime = SweetieBotRuntime()
    runtime.note_turn("Hello!", "Hi there!", mood="warm")
    state = runtime.character_state()
    assert state["last_input"] == "Hello!"
    assert state["last_reply"] == "Hi there!"
    assert state["mood"] == "warm"
    assert state["turn_count"] == 1

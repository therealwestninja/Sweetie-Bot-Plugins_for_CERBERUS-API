from sweetiebot.memory.models import MemoryQuery, MemoryRecord
from sweetiebot.plugins.builtins.memory import InMemoryStorePlugin, SQLiteMemoryStorePlugin
from sweetiebot.runtime import SweetieBotRuntime


def test_inmemory_store_roundtrip():
    store = InMemoryStorePlugin()
    store.put(MemoryRecord(kind="fact", content="Sweetie Bot likes singing"))
    results = store.query(MemoryQuery(text="singing"))
    assert len(results) == 1
    assert results[0].kind == "fact"


def test_sqlite_store_roundtrip():
    store = SQLiteMemoryStorePlugin()
    store.configure({"path": ":memory:"})
    store.put(MemoryRecord(kind="fact", content="Diamond Tiara cameo"))
    results = store.query(MemoryQuery(text="cameo"))
    assert len(results) == 1
    assert results[0].content == "Diamond Tiara cameo"
    store.shutdown()


def test_runtime_note_turn_writes_memory():
    runtime = SweetieBotRuntime()
    runtime.note_turn("Hello Sweetie Bot", "Hi there!")
    items = runtime.recall(limit=5)
    kinds = {item["kind"] for item in items}
    assert "user_input" in kinds
    assert "assistant_reply" in kinds

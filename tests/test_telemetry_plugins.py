from sweetiebot.plugins.builtins.telemetry import InMemoryTelemetrySinkPlugin
from sweetiebot.runtime import SweetieBotRuntime
from sweetiebot.telemetry.models import TraceEvent


def test_inmemory_telemetry_sink_roundtrip():
    sink = InMemoryTelemetrySinkPlugin()
    sink.emit(TraceEvent(event_type="test_event", message="Telemetry test"))
    events = sink.recent_events(limit=5)
    assert len(events) == 1
    assert events[0].event_type == "test_event"


def test_runtime_emits_trace_events():
    runtime = SweetieBotRuntime()
    runtime.apply_mood_event("greet")
    events = runtime.recent_trace_events(limit=20)
    event_types = {event["event_type"] for event in events}
    assert "runtime_initialized" in event_types
    assert "mood_event_applied" in event_types

from sweetiebot.routines.registry import RoutineRegistry


def test_routine_registry():
    registry = RoutineRegistry()
    registry.register("demo", {"title": "Demo"})
    assert registry.get("demo")["title"] == "Demo"

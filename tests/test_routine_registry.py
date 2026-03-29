from pathlib import Path

from sweetiebot.routines.registry import RoutineRegistry


def test_registry_normalizes_author_friendly_steps(tmp_path: Path) -> None:
    path = tmp_path / "greet_guest.yaml"
    path.write_text(
        """
summary: Friendly hello
steps:
  - speak: Hi there!
  - emote: happy_bounce
  - pause_ms: 600
""".strip(),
        encoding="utf-8",
    )
    registry = RoutineRegistry()
    registry.register_from_yaml(path)
    routine = registry.get("greet_guest")
    assert routine is not None
    assert routine["title"] == "Greet Guest"
    assert routine["step_count"] == 3
    assert routine["steps"][0]["type"] == "speak"
    assert routine["steps"][1]["type"] == "emote"
    assert routine["estimated_duration_ms"] >= 2300

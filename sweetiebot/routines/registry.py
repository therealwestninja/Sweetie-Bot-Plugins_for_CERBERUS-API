from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sweetiebot.errors import ValidationError
from sweetiebot.observability import EventLogger
from sweetiebot.routines.models import RoutineModel

_logger = EventLogger(__name__)


def load_routines_file(path: str | Path) -> list[RoutineModel]:
    file_path = Path(path)
    try:
        data: Any = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise ValidationError(f"Routine file not found: {file_path}") from exc

    routines = data.get("routines", [])
    if not isinstance(routines, list):
        _logger.validation_failed("routines", "Expected 'routines' to be a list", payload=data)
        raise ValidationError(f"Invalid routine file {file_path}: 'routines' must be a list")

    result = []
    for item in routines:
        try:
            result.append(RoutineModel.model_validate(item))
        except Exception as exc:
            _logger.validation_failed("routines", str(exc), payload=item)
            raise ValidationError(f"Invalid routine entry in {file_path}: {exc}") from exc
    return result

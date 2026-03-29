from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sweetiebot.errors import ValidationError
from sweetiebot.observability import EventLogger
from sweetiebot.persona.models import PersonaModel

_logger = EventLogger(__name__)


def load_persona_file(path: str | Path) -> PersonaModel:
    file_path = Path(path)
    try:
        data: Any = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise ValidationError(f"Persona file not found: {file_path}") from exc

    try:
        return PersonaModel.model_validate(data)
    except Exception as exc:
        _logger.validation_failed("persona", str(exc), payload=data)
        raise ValidationError(f"Invalid persona file {file_path}: {exc}") from exc

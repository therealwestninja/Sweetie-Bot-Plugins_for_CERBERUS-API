from __future__ import annotations

class SweetieBotError(Exception):
    """Base exception for Sweetie Bot."""

class ValidationError(SweetieBotError):
    """Raised when user-supplied or asset data is invalid."""

class ConfigurationError(SweetieBotError):
    """Raised when runtime or plugin configuration is invalid."""

class PluginError(SweetieBotError):
    """Raised when a plugin fails to load or execute."""

class DialogueError(SweetieBotError):
    """Raised when dialogue generation fails."""

class RoutineError(SweetieBotError):
    """Raised when a routine payload cannot be used."""

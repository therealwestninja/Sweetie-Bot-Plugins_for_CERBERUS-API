from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RuntimePlugin(Protocol):
    """Small reusable contract for runtime plugins.

    The real CERBERUS plugin system is richer; this scaffold keeps the surface
    intentionally tiny so plugin logic stays portable while the upstream
    integration is still being mapped out.
    """

    name: str

    def describe(self) -> dict: ...

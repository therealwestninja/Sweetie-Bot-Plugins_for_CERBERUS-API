from dataclasses import dataclass


@dataclass
class AttentionTarget:
    id: str
    kind: str
    confidence: float


class AttentionManager:
    def __init__(self) -> None:
        self.current: AttentionTarget | None = None

    def update(self, target: AttentionTarget | None) -> None:
        self.current = target

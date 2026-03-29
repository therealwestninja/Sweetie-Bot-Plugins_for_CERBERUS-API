from dataclasses import dataclass
from time import monotonic


@dataclass
class SyncCue:
    kind: str
    starts_at: float
    ends_at: float | None = None


class CueSynchronizer:
    def __init__(self) -> None:
        self._cues: list[SyncCue] = []

    def start(self, kind: str) -> SyncCue:
        cue = SyncCue(kind=kind, starts_at=monotonic())
        self._cues.append(cue)
        return cue

    def end(self, cue: SyncCue) -> SyncCue:
        cue.ends_at = monotonic()
        return cue

    @property
    def cues(self) -> list[SyncCue]:
        return list(self._cues)

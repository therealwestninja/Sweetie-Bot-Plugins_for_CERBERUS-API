from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, Any, List

def now():
    return datetime.now(UTC).isoformat()

@dataclass
class Track:
    track_id: str
    label: str
    confidence: float
    position: Dict[str, float]
    tags: List[str]
    last_seen: str
    source: str

    def dump(self):
        return {
            "track_id": self.track_id,
            "label": self.label,
            "confidence": self.confidence,
            "position": self.position,
            "tags": self.tags,
            "last_seen": self.last_seen,
            "source": self.source,
        }

@dataclass
class TrackerState:
    tracks: Dict[str, Track] = field(default_factory=dict)
    events: List[dict] = field(default_factory=list)

state = TrackerState()

def upsert_detection(det, source):
    # if provided id use it, else create new track
    track_id = det.id or f"{det.label}-{uuid.uuid4()}"
    t = state.tracks.get(track_id)
    if not t:
        t = Track(track_id, det.label, det.confidence, det.position, det.tags, now(), source)
        state.tracks[track_id] = t
        event_type = f"vision.{det.label}_detected"
    else:
        t.confidence = det.confidence
        t.position = det.position
        t.tags = det.tags
        t.last_seen = now()
        t.source = source
        event_type = f"vision.{det.label}_updated"
    event = {
        "event_id": str(uuid.uuid4()),
        "topic": event_type,
        "source": source,
        "payload": t.dump(),
        "created_at": now(),
    }
    state.events.append(event)
    state.events = state.events[-200:]
    return t.dump(), event

def ingest(detections, source, scene):
    outputs = []
    events = []
    for det in detections:
        t, e = upsert_detection(det, source)
        outputs.append(t)
        events.append(e)
    if scene:
        events.append({
            "event_id": str(uuid.uuid4()),
            "topic": "vision.scene_update",
            "source": source,
            "payload": scene,
            "created_at": now(),
        })
    return outputs, events

def list_tracks():
    return [t.dump() for t in state.tracks.values()]

def get_track(track_id):
    t = state.tracks.get(track_id)
    return t.dump() if t else None

def reset():
    state.tracks.clear()
    state.events.clear()
    return {"status":"reset"}

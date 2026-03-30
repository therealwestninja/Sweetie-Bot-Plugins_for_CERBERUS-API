from __future__ import annotations

import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List

from app.config import settings

def now_iso() -> str:
    return datetime.now(UTC).isoformat()

def topic_matches(pattern: str, topic: str) -> bool:
    if pattern.endswith("*"):
        return topic.startswith(pattern[:-1])
    return pattern == topic

@dataclass
class EventBusState:
    subscribers: Dict[str, list[str]] = field(default_factory=dict)
    queues: Dict[str, deque] = field(default_factory=dict)
    recent_events: deque = field(default_factory=lambda: deque(maxlen=settings.max_recent_events))
    published_count: int = 0

state = EventBusState()

def subscribe(subscriber_id: str, topics: list[str]) -> dict:
    state.subscribers[subscriber_id] = topics[:]
    state.queues.setdefault(subscriber_id, deque())
    return {"subscriber_id": subscriber_id, "topics": topics}

def unsubscribe(subscriber_id: str) -> dict:
    removed = subscriber_id in state.subscribers
    state.subscribers.pop(subscriber_id, None)
    state.queues.pop(subscriber_id, None)
    return {"subscriber_id": subscriber_id, "removed": removed}

def publish(topic: str, source: str, payload: dict, tags: list[str]) -> dict:
    event = {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "source": source,
        "payload": payload,
        "tags": tags,
        "created_at": now_iso(),
    }
    delivered_to = []
    for subscriber_id, patterns in state.subscribers.items():
        if any(topic_matches(pattern, topic) for pattern in patterns):
            state.queues.setdefault(subscriber_id, deque()).append(event)
            delivered_to.append(subscriber_id)
    state.recent_events.appendleft(event)
    state.published_count += 1
    return {"event": event, "delivered_to": delivered_to}

def poll(subscriber_id: str, limit: int) -> dict:
    queue = state.queues.get(subscriber_id)
    if queue is None:
        return {"subscriber_id": subscriber_id, "events": [], "remaining": 0}
    out = []
    for _ in range(max(0, limit)):
        if not queue:
            break
        out.append(queue.popleft())
    return {"subscriber_id": subscriber_id, "events": out, "remaining": len(queue)}

def recent(limit: int = 25) -> list[dict]:
    return list(list(state.recent_events)[:limit])

def clear() -> dict:
    sub_count = len(state.subscribers)
    queue_count = len(state.queues)
    state.subscribers.clear()
    state.queues.clear()
    state.recent_events.clear()
    state.published_count = 0
    return {"cleared_subscribers": sub_count, "cleared_queues": queue_count}

def status() -> dict:
    return {
        "subscriber_count": len(state.subscribers),
        "queue_count": len(state.queues),
        "published_count": state.published_count,
        "recent_event_count": len(state.recent_events),
        "subscribers": {k: v for k, v in state.subscribers.items()},
    }

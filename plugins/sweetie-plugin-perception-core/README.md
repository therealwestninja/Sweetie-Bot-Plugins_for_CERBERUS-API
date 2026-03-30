# sweetie-plugin-perception-core

Perception ingestion + tracking + standardized event emitter for Sweetie-Bot.

## What it does
- accepts detections (persons/objects/scenes)
- assigns/maintains track IDs
- keeps last-known positions and confidence
- emits normalized events for the event-bus
- provides track query endpoints

## Expected upstream
Any vision system can POST detections to this plugin.

## Emits (recommended to event-bus)
- vision.person_detected
- vision.object_detected
- vision.scene_update
- vision.target_lost

## Example ingest

{
  "type": "perception.ingest",
  "payload": {
    "source": "vision.detector",
    "detections": [
      {"label":"person","id":"person-001","confidence":0.92,"position":{"x":1.2,"y":0.4},"tags":["operator"]},
      {"label":"charging_dock","confidence":0.88,"position":{"x":-0.5,"y":2.1}}
    ],
    "scene": {"room":"living_room"}
  }
}

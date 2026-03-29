# Event Contract

The event stream uses a lightweight envelope so the operator console can stay simple while the robot-side runtime evolves.

## Envelope

```json
{
  "type": "persona.selected",
  "timestamp": "2026-03-29T00:00:00Z",
  "source": "sweetiebot_persona",
  "payload": {}
}
```

## Current event types

### `events.snapshot`
Bootstrap payload sent to new WebSocket clients.

### `events.keepalive`
Idle heartbeat sent while no other events are pending.

### `persona.selected`
Emitted when the active persona preset changes.

### `dialogue.reply_ready`
Emitted when a line has been interpreted and a reply has been generated.

### `attention.target_changed`
Emitted when the active social target changes.

### `routine.started`
Emitted when a routine starts.

### `routine.completed`
Emitted when a routine is cancelled or finishes.

### `persona.changed`
Currently used for mood-driven emote events emitted by the emote plugin.

## Notes

- Event payloads include `character` when a UI refresh should happen immediately.
- The scaffold intentionally favors legible JSON over a more compressed protocol.
- A future CERBERUS integration may map these payloads onto the upstream event bus instead of emitting them directly.

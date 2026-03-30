# sweetie-plugin-event-bus

A reusable typed event spine for Sweetie-Bot / CERBERUS.

This plugin is the missing reaction layer between:
- perception
- memory
- missions
- autonomy
- world model
- controller UI actions
- future learning loops

## Why this exists

Without an event bus:
- each plugin has to call every other plugin directly
- reactions become tangled
- behavior loops are harder to inspect
- cross-plugin logic gets duplicated

With an event bus:
- plugins publish events once
- other systems subscribe to topics
- the controller or backend can poll for pending events
- reaction logic becomes composable

## Supported execute actions

- `event.publish`
- `event.subscribe`
- `event.unsubscribe`
- `event.poll`
- `event.recent`
- `event.clear`
- `event.status`

## Event model

Each event looks like:

```json
{
  "topic": "vision.person_detected",
  "source": "vision.detector",
  "payload": {
    "id": "person-001",
    "confidence": 0.92
  },
  "tags": ["person", "operator"]
}
```

## Subscription model

Each subscriber registers:
- `subscriber_id`
- `topics`

Topics can be exact matches or prefix wildcards ending in `*`.

Examples:
- `vision.person_detected`
- `vision.*`
- `memory.*`
- `runtime.follow_*`

## Quick start

### Local
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 7000
```

### Docker
```bash
docker build -t sweetie-plugin-event-bus .
docker run --rm -p 7000:7000 --env-file .env.example sweetie-plugin-event-bus
```

## Example: subscribe

```bash
curl -X POST http://localhost:7000/execute   -H "Content-Type: application/json"   -d '{
    "type": "event.subscribe",
    "payload": {
      "subscriber_id": "memory-watcher",
      "topics": ["vision.*", "world.*"]
    }
  }'
```

## Example: publish

```json
{
  "type": "event.publish",
  "payload": {
    "topic": "vision.person_detected",
    "source": "vision.detector",
    "payload": {
      "id": "person-001",
      "confidence": 0.92
    },
    "tags": ["person", "operator"]
  }
}
```

## Example: poll

```json
{
  "type": "event.poll",
  "payload": {
    "subscriber_id": "memory-watcher",
    "limit": 10
  }
}
```

## Why this matters

This plugin is one of the most important architecture layers in the whole ecosystem.

It creates the path toward:
- action/reaction loops
- asynchronous plugin coordination
- event-driven memory updates
- reactive missions
- safer AI behavior composition

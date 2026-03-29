# API Contract

This document describes the current scaffold API, not the final hardware runtime.

## Read endpoints

### `GET /`
Returns service metadata, current character state, and recent events.

### `GET /character`
Returns the active in-memory character state.

### `GET /character/personas`
Returns the available persona presets loaded from `sweetiebot-assets/persona/*.yaml`.

### `GET /attention`
Returns the active attention target summary.

### `GET /routines`
Returns routine ids plus expanded routine metadata loaded from YAML assets.

### `GET /memory/summary`
Returns the memory summary used by the operator console.

### `GET /accessories`
Returns currently declared accessory capabilities.

### `GET /plugins`
Returns metadata describing the reusable Sweetie-Bot plugins loaded into the scaffold runtime.

### `GET /events`
Returns recent event history from the in-memory event bus.

## Command endpoints

### `POST /character/say`
Input:

```json
{ "text": "hello sweetie bot" }
```

Returns a dialogue reply, detected intent, linked emote id, and resulting character state.

### `POST /character/emote`
Input:

```json
{ "emote_id": "happy_bounce" }
```

If `emote_id` is omitted, the runtime selects an emote from the current mood.

### `POST /character/routine`
Input:

```json
{ "routine_id": "greeting_01" }
```

Returns routine metadata including title, steps, and step count.

### `POST /character/focus`
Input:

```json
{ "target_id": "nearest_person", "confidence": 1.0, "mode": "person" }
```

### `POST /character/persona`
Input:

```json
{ "persona_id": "sweetiebot_convention" }
```

### `POST /character/cancel`
Stops speaking and clears the active routine.

## Event stream

### `WS /ws/events`
Sends:
- an initial `events.snapshot`
- incremental events for persona, dialogue, attention, routines, and emotes
- keepalive messages while idle

## Contract status

Prototype, but live and tested.

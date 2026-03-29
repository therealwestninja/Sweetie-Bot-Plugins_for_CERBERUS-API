# API Contract

## Character

### `GET /character`
Return the current character state.

### `GET /character/personas`
Return available persona presets.

### `POST /character/persona`
Switch the active persona.

### `GET /character/llm`
Return the active dialogue provider, configured model, and CERBERUS audio sink status.

### `POST /character/say`
Accept a text utterance, generate an in-character reply, and attempt audio dispatch.

Example response:

```json
{
  "heard": "hello",
  "reply": "Hi everypony! Show mode is live and I am ready to sparkle.",
  "intent": "greet",
  "emote_id": "curious_headtilt",
  "provider": "openai",
  "model": "gpt-5.4",
  "audio": {
    "ok": true,
    "sink": "cerberus_go2_onboard_audio",
    "detail": "speech dispatched",
    "status_code": 200
  }
}
```

## Plugins

### `GET /plugins`
Return plugin inventory and declared capabilities.

## Events

### `GET /events`
Return recent event history.

### `WS /ws/events`
Return a live stream of snapshots and state-change events.

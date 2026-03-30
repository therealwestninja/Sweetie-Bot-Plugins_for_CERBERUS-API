# sweetie-plugin-stt-router

A reusable speech-to-text and utterance interpretation layer for Sweetie-Bot.

## What it does

- normalizes speech-input requests behind a stable plugin contract
- supports raw transcript ingestion now
- classifies utterances into simple command/chat categories
- extracts lightweight speech intent hints for Sweetie’s interaction loop
- keeps provider swaps behind one stable interface

## Why this matters

Sweetie now has:
- perception
- cognition
- interaction
- behavior
- safety
- TTS voice output

This plugin gives her the matching hearing/input layer, so spoken operator interaction can be turned into transcript + intent data.

## Supported execute actions

- `stt.transcribe`
- `stt.process_utterance`
- `stt.list_providers`
- `stt.set_defaults`
- `stt.get_defaults`
- `stt.status`

## Example input

```json
{
  "type": "stt.process_utterance",
  "payload": {
    "transcript": "Sweetie, follow me please.",
    "speaker_id": "operator-001"
  }
}
```

## Example output

```json
{
  "transcript": "Sweetie, follow me please.",
  "intent_type": "command",
  "command_name": "follow_operator",
  "confidence": 0.91,
  "entities": {
    "target": "speaker"
  }
}
```

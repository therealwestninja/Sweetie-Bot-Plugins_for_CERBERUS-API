# sweetie-plugin-tts-router

A reusable text-to-speech routing layer for Sweetie-Bot.

## What it does

- normalizes speech requests from interaction-core and behavior-engine
- picks a voice profile
- shapes rate, pitch, and style tags
- returns a synthesis-ready envelope
- supports mock/local/provider-based TTS routing later without changing the controller contract

## Why this matters

Sweetie now has:
- perception
- cognition
- interaction
- behavior
- safety

This plugin gives her a voice layer, so character-consistent speech can become actual audio output.

## Supported execute actions

- `tts.speak`
- `tts.preview_voice`
- `tts.list_voices`
- `tts.set_defaults`
- `tts.get_defaults`
- `tts.status`

## Example input

```json
{
  "type": "tts.speak",
  "payload": {
    "text": "Ooo! There you are! I'll come with you!",
    "tone": "bright_cheerful",
    "emotion": "excited"
  }
}
```

## Example output

```json
{
  "provider": "mock",
  "voice": "sweetie_bright",
  "text": "Ooo! There you are! I'll come with you!",
  "rate": 1.12,
  "pitch": 1.18,
  "style_tags": ["youthful", "playful", "wholesome", "excited"]
}
```

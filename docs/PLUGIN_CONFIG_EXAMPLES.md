# Plugin Config Examples

## Speech / Audio Plugin Configuration

Sweetie Bot can be configured with a TTS provider plugin and an audio output plugin.
These plugins should stay high-level and safe for local testing and later CERBERUS handoff.

### Example

```yaml
plugins:
  sweetiebot.mock_tts:
    enabled: true
    default_voice: sweetie
    cache_dir: .cache/tts
    max_chars: 160

  sweetiebot.mock_audio_output:
    enabled: true
    device_name: default
    playback_mode: immediate
    allow_file_export: true
```

## Recommended Config Keys

### `tts_provider`
- `enabled`: bool
- `default_voice`: string
- `cache_dir`: string
- `max_chars`: integer
- `speaking_rate`: float
- `pitch`: float

### `audio_output`
- `enabled`: bool
- `device_name`: string
- `playback_mode`: string (`immediate`, `queued`, `silent`)
- `allow_file_export`: bool
- `volume`: float

## Future Expansion

Later production implementations may add:
- interruptible playback
- queue prioritization
- voice profile packs
- CERBERUS audio relay
- subtitle/transcript mirroring

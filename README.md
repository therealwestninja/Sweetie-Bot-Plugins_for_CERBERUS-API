# Sweetie Bot Patch Bundle v6

This patch continues the **easy / low-friction** work first.

## Added in this bundle

### Plugin health + richer status reporting
- `sweetiebot/plugins/health.py`
- richer plugin health snapshots
- registry-wide status summary helpers
- standardized runtime-friendly plugin diagnostics

### Mock speech interfaces
- `tts_provider` plugin family
- `audio_output` plugin family
- built-in mock TTS provider
- built-in mock audio output plugin

### Runtime integration
- runtime now exposes:
  - speech-capable plugin summary
  - mock speech synthesis pathway
  - mock audio playback pathway
- intended for safe local testing before CERBERUS integration

### Tests
- plugin registry health summary
- mock TTS synthesis result shape
- mock audio output playback result shape

## Merge notes

These files are written as a patch-style drop-in bundle for the repo layout that has been developed so far.
Extract into the repo root and review/merge as needed.

# Plugins

This directory holds **CERBERUS-style runtime plugins** for Sweetie-Bot.

The current scaffold keeps the contract intentionally small so the useful logic
can be lifted into a real CERBERUS host later without dragging along the entire
prototype runtime.

## Included plugins

- `sweetiebot_persona` — persona selection and mood shaping
- `sweetiebot_dialogue` — reply generation and intent tagging
- `sweetiebot_attention` — attention target updates
- `sweetiebot_emotes` — mood to emote mapping
- `sweetiebot_routines` — routine start metadata and step summaries

## Design rules

- Plugins return plain dictionaries.
- Plugins do not own transport, HTTP, or WebSocket state.
- Plugins do not directly command hardware.
- Plugins are written to be reusable inside a richer CERBERUS plugin host.

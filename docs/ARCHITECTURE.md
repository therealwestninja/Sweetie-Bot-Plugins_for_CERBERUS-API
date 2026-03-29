# Architecture

## Intent

Sweetie Bot is built as a thin character layer over a CERBERUS-style runtime. The API layer owns authoritative robot state, routines, plugin hosting, event streaming, and hardware adapters. The web layer is an operator console and authoring surface.

## Runtime split

### `upstream_api/`
- FastAPI scaffold
- runtime state host
- plugin inventory
- event bus
- LLM provider selection
- CERBERUS audio adapter

### `plugins/`
Reusable modules that can be transplanted into other CERBERUS forks:
- `sweetiebot_persona`
- `sweetiebot_dialogue`
- `sweetiebot_attention`
- `sweetiebot_emotes`
- `sweetiebot_routines`
- `sweetiebot_accessories`

### `sweetiebot/`
Shared, repo-local runtime code:
- dialogue manager and provider adapters
- accessory audio adapter
- persona loading and state logic
- emote mapping
- routine registry

### `upstream-web/`
Browser-side operator console scaffold with:
- persona switching
- dialogue testing
- routine triggering
- plugin inventory
- live event stream
- LLM and audio status panel

## Dialogue path

1. operator or user text enters `/character/say`
2. `sweetiebot_dialogue` chooses the active provider
3. provider generates a short in-character reply
4. reply metadata is returned to the caller
5. the reply is optionally forwarded to the CERBERUS audio endpoint for onboard playback
6. `dialogue.reply_ready` is emitted to the live event stream

## Why plugin-heavy?

This repo is trying to stay useful outside Sweetie Bot. Persona selection, LLM-backed short-form dialogue, routine metadata, and CERBERUS audio dispatch are all generic enough to be useful to other character robot projects.

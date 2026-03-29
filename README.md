# Sweetie Bot Fork

A GitHub-ready scaffold for building a character-driven robot companion on top of the CERBERUS API and web controller stack.

This repo keeps the control plane small and reusable: robot motion, safety, and bridge concerns stay in the CERBERUS-style API layer, while Sweetie Bot personality, routines, dialogue, and accessory adapters are implemented as transplantable plugins.

## Current status

`v0.0.7` is still a scaffold, but it now includes a working end-to-end personality slice:

- FastAPI scaffold with character, routine, memory, accessory, plugin, and event endpoints
- reusable Sweetie Bot plugins for persona, dialogue, attention, emotes, routines, and accessories
- selectable dialogue backends:
  - local rule-based fallback
  - OpenAI Responses API adapter
  - Anthropic Messages API adapter
- configurable CERBERUS audio adapter that can forward spoken replies to a Go2 onboard audio endpoint
- browser-side operator console scaffold with live event streaming and LLM/audio status

## Repo layout

```text
upstream_api/      # API/runtime scaffold that mirrors a CERBERUS-style host
upstream-web/      # Browser controller scaffold
plugins/           # Reusable personality and behavior plugins
sweetiebot/        # Shared character runtime modules
sweetiebot-assets/ # Persona, emote, routine, and prompt content
sweetiebot-ops/    # Deployment and ops scaffolding
```

## Quick start

### API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m upstream_api.app.main
```

### Web scaffold

Open `upstream-web/src/index.html` in a simple local static server and point it at the API base URL.

## Personality backends

By default, the project uses the local rule-based dialogue manager. To switch to an API-backed personality layer, set one of the following:

### OpenAI

```bash
export SWEETIEBOT_LLM_PROVIDER=openai
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-5.4
```

### Anthropic

```bash
export SWEETIEBOT_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=your_key_here
export ANTHROPIC_MODEL=claude-sonnet-4-5
```

### CERBERUS / Go2 onboard audio

```bash
export CERBERUS_AUDIO_BASE_URL=http://127.0.0.1:9000
export CERBERUS_AUDIO_PATH=/audio/speak
export CERBERUS_AUDIO_VOICE=sweetie-default
```

The audio adapter is intentionally configurable because CERBERUS forks often expose hardware features through slightly different routes.

## Useful endpoints

- `GET /character`
- `GET /character/personas`
- `GET /character/llm`
- `POST /character/say`
- `POST /character/persona`
- `GET /plugins`
- `GET /events`
- `WS /ws/events`

## Development notes

This project is intentionally puzzle-shaped. The goal is to build small, testable slices first:

1. persona and mood shaping
2. dialogue and speech
3. routines and choreography
4. attention and social behaviors
5. hardware-specific polish

## Documentation

- [Vision](docs/VISION.md)
- [Roadmap](docs/ROADMAP.md)
- [Requirements](docs/REQUIREMENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API contract](docs/contracts/API.md)
- [Event contract](docs/contracts/EVENTS.md)
- [Changelog](CHANGELOG.md)

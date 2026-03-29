# Sweetie Bot Fork

Sweetie Bot Fork is a GitHub-ready scaffold for building a character-driven robot companion on top of a CERBERUS-style API and web controller stack.

The project keeps the hard real-time control plane small and reusable. Motion, safety, bridges, and hardware coordination stay in the CERBERUS-facing runtime. Personality, emotes, routines, accessories, and dialogue are built as reusable plugins that other CERBERUS-based projects can transplant.

## Highlights

- FastAPI runtime scaffold with character, routine, accessory, event, plugin, and memory endpoints
- reusable Sweetie Bot plugins for persona, dialogue, attention, emotes, routines, and accessories
- local rule-based dialogue plus adapter scaffolds for OpenAI and Anthropic
- configurable CERBERUS audio sink for Go2 onboard speech output
- browser-side operator console scaffold with live event streaming
- asset-driven personas, routines, accessory scenes, and emote metadata

## Repository layout

```text
upstream_api/      CERBERUS-style API/runtime scaffold
upstream-web/      Browser controller scaffold
plugins/           Reusable CERBERUS-style plugins
sweetiebot/        Shared runtime modules
sweetiebot-assets/ Persona, emote, routine, accessory, and prompt assets
sweetiebot-ops/    Deployment and operations scaffolding
docs/              Vision, roadmap, contracts, and architecture notes
```

## Current status

Version `0.0.8` focuses on foundation work for the most reusable parts of the stack: **persona, emotes, routines, and accessories**.

New in this pass:
- persona profiles now define default emotes, accessory scenes, and routine tags
- emotes are resolved through a reusable expression plugin with body profiles and accessory scene application
- routines can now be previewed as a simple execution plan before they are started
- accessories are exposed as reusable scene assets rather than a flat capability blob
- runtime endpoints now expose foundation data for authoring and controller UIs

## Quick start

### API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m upstream_api.app.main
```

### Web scaffold

Serve `upstream-web/src/` from any simple static file server and point it at the API base URL.

## Personality backends

The default backend is local and deterministic, which keeps scaffolding easy to test. To switch the personality layer to an API-backed provider:

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

## CERBERUS / Go2 onboard audio

```bash
export CERBERUS_AUDIO_BASE_URL=http://127.0.0.1:9000
export CERBERUS_AUDIO_PATH=/audio/speak
export CERBERUS_AUDIO_VOICE=sweetie-default
```

## Useful endpoints

- `GET /character`
- `GET /character/personas`
- `GET /character/foundation`
- `GET /character/llm`
- `POST /character/persona`
- `POST /character/say`
- `POST /character/emote`
- `GET /emotes`
- `GET /routines`
- `GET /routines/{routine_id}/plan`
- `GET /accessories`
- `GET /accessories/scenes`
- `POST /accessories/scene`
- `GET /plugins`
- `GET /events`
- `WS /ws/events`

## Development approach

This repo is intentionally built in small, testable slices. The current priority order is:

1. reusable persona and mood shaping
2. emote resolution and accessory scene application
3. routine planning and choreography metadata
4. dialogue and speech queueing
5. hardware-specific polish for a real CERBERUS fork

## Documentation

- [Vision](docs/VISION.md)
- [Roadmap](docs/ROADMAP.md)
- [Requirements](docs/REQUIREMENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API contract](docs/contracts/API.md)
- [Assets contract](docs/contracts/ASSETS.md)
- [Routines contract](docs/contracts/ROUTINES.md)
- [Changelog](CHANGELOG.md)

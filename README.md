# Sweetie-Bot Fork

A playful, convention-first character robot scaffold built on top of a **CERBERUS / Unitree Go2** style runtime.

Sweetie-Bot is not trying to replace the upstream control stack. The goal is to keep the robot runtime recognizable, safety-first, and merge-friendly while layering on the things that make a character robot feel alive: persona presets, dialogue, attention, emotes, routines, and a lightweight operator console.

> Current state: early prototype scaffold with a working in-memory API, reusable plugin-style modules, live event streaming, persona switching, and a tiny browser operator console.

## Why this repo exists

This repo is the "smallest useful slice" of a bigger build:

- keep the **robot runtime** separate from the **character layer**
- prototype high-level character behavior as **reusable CERBERUS-style plugins**
- prove API contracts and event contracts before hardware integration gets messy
- treat choreography, persona data, and dialogue as **assets**, not hard-coded chaos
- build toward a polished **convention demo** before chasing an open-ended companion robot

## What works today

### API scaffold

Run the FastAPI scaffold and you get:

- character state endpoints
- persona preset listing and switching
- emote triggering
- routine triggering with real step metadata loaded from YAML assets
- attention targeting
- memory and accessory summary endpoints
- plugin inventory endpoint
- recent events endpoint
- live WebSocket stream at `/ws/events`

### Pluginized character layer

The current pass moves more of the interesting behavior into reusable plugin-like modules:

- `sweetiebot_persona` — persona selection and mood shaping
- `sweetiebot_dialogue` — reply generation and intent tagging
- `sweetiebot_attention` — social target updates
- `sweetiebot_emotes` — mood-to-emote mapping with accessory hints
- `sweetiebot_routines` — routine start metadata and step summaries

These plugins are intentionally plain-Python and transport-agnostic so they can be transplanted into a richer CERBERUS plugin host later.

### Web operator console

The browser scaffold includes:

- live character state
- dialogue test bench
- persona preset buttons
- routine launcher with step counts
- accessory summary
- memory summary
- plugin inventory view
- live activity log driven by WebSocket events

## Repository layout

```text
sweetiebot-fork/
├── upstream-api/                  # tracked integration surface for CERBERUS API docs/stubs
├── upstream-web/                  # tracked integration surface for CERBERUS web docs/stubs
├── upstream_api/                  # working FastAPI scaffold used in this repo
├── sweetiebot/                    # core character-layer code
├── plugins/                       # reusable CERBERUS-style runtime plugins
├── sweetiebot-assets/             # persona, emotes, routines, dialogue prompts
├── sweetiebot-ops/                # deployment/runbooks/replay tooling stubs
├── docs/                          # roadmap, architecture, contracts, safety, vision
├── tests/                         # scaffold and contract tests
└── scripts/                       # dev helpers and GitHub seeding helpers
```

## Quick start

### API

```bash
python -m upstream_api.app.main
```

The API starts on `http://127.0.0.1:8080` by default.

### Web console

Serve `upstream-web/src/` with any static file server and open `index.html`.
The console defaults to `http://127.0.0.1:8080`, and you can change the base URL in the UI.

## API surface

### Read endpoints

- `GET /`
- `GET /character`
- `GET /character/personas`
- `GET /attention`
- `GET /routines`
- `GET /memory/summary`
- `GET /accessories`
- `GET /plugins`
- `GET /events`

### Command endpoints

- `POST /character/say`
- `POST /character/emote`
- `POST /character/routine`
- `POST /character/focus`
- `POST /character/persona`
- `POST /character/cancel`

### Event stream

- `WS /ws/events`

The stream sends a bootstrap snapshot, then forwards persona, dialogue, attention, routine, and emote events.

## Design principles

1. **Fork, do not rewrite.**
2. **Safety always beats charm.**
3. **Character logic should be reusable.**
4. **Assets belong in data files whenever possible.**
5. **Perception informs behavior but does not directly command hardware.**
6. **Convention demo quality comes before open-ended autonomy.**

## Roadmap snapshot

### Current milestone
- scaffold the reusable character layer
- keep the API tiny but real
- keep the web console useful enough for operator testing

### Next milestone
- routine step playback planning
- richer memory and preference editing
- better plugin host abstraction
- operator "show mode" UI

## Documentation

- [Vision](docs/VISION.md)
- [Roadmap](docs/ROADMAP.md)
- [Requirements](docs/REQUIREMENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Contract](docs/contracts/API.md)
- [Event Contract](docs/contracts/EVENTS.md)
- [Safety Case](docs/SAFETY_CASE.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Development

```bash
pytest
ruff check .
```

## Status

- version: `0.0.6`
- maturity: prototype scaffold
- hardware status: not wired to a real robot yet
- intended audience: collaborators building the character layer on top of CERBERUS

## License

MIT for the scaffold in this repository. Respect the licenses of upstream projects and any third-party assets you add later.

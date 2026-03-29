# Sweetie-Bot Fork
> Aspirational character-robot monorepo for a CERBERUS/Unitree Go2-based "Sweetie-Bot" build.

This repository is an **aspirational scaffold** for a staged, convention-first, companion-later character robot project.
It is designed to:

- preserve an upstream robotics/runtime core
- preserve an upstream web/operator console
- add a **Sweetie-Bot character layer**
- separate runtime code from character assets and operational tooling
- stay merge-friendly and documentation-heavy from day one

## Status
**Version:** 0.0.3  
**State:** early working scaffold / API + controller slice / non-production

This repo intentionally contains:
- structure
- documentation
- interface contracts
- placeholder modules
- sample schemas
- sample plugin code
- starter assets
- stubs for future implementation

It intentionally does **not** claim to be a working robot runtime.

It now includes a **tiny working in-memory API scaffold** and a **browser-side operator console scaffold** for the first API/controller slice.

## Monorepo layout

```text
sweetiebot-fork/
├── upstream-api/                  # tracked integration surface for CERBERUS API
├── upstream-web/                  # tracked integration surface for CERBERUS web UI
├── sweetiebot/                    # character-layer code
├── plugins/                       # Sweetie-Bot runtime plugins
├── sweetiebot-assets/             # persona, dialogue, emotes, routines, prompts
├── sweetiebot-ops/                # deploy/replay/runbooks
├── docs/                          # roadmap, vision, ADRs, safety, architecture
├── tools/                         # extractors, packagers, log-review helpers
├── tests/                         # contract and scaffold tests
└── scripts/                       # bootstrap, packaging, dev helpers
```

## Design principles

1. **Fork, do not rewrite.**
2. **Safety always beats charm.**
3. **Convention demo before open-ended companion.**
4. **Character content is data, not hard-coded behavior.**
5. **Perception informs behavior, but does not directly command actuators.**
6. **All high-level actions funnel through the robot runtime and safety layers.**

## Repo goals

- give the project a clean starting point for GitHub
- define ownership boundaries between runtime, UI, assets, and operations
- make future implementation less chaotic
- document intended interfaces before deep coding begins

## Quick start

```bash
git clone <your-fork-url>
cd sweetiebot-fork
python scripts/bootstrap.py
python scripts/tree.py
```

## First coded slice

Run the scaffold API:

```bash
python -m upstream_api.app.main
```

Then open `upstream-web/src/index.html` in a local static server, or serve it with your preferred frontend dev tool, and point it at `http://127.0.0.1:8080`.

Implemented in this slice:
- `GET /`
- `GET /character`
- `GET /attention`
- `GET /routines`
- `GET /memory/summary`
- `GET /accessories`
- `POST /character/say`
- `POST /character/emote`
- `POST /character/routine`
- `POST /character/focus`
- `POST /character/cancel`

## Important note

This repository is a **starter skeleton** only. Before becoming real:
- wire it to actual upstream repositories
- replace placeholders with real integration code
- validate sim vs hardware behavior
- build and enforce a real safety case
- test every motion on hardware before public use

## Documents

- [Vision](docs/VISION.md)
- [Roadmap](docs/ROADMAP.md)
- [Requirements](docs/REQUIREMENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Safety Case](docs/SAFETY_CASE.md)

## Release
Initial aspirational scaffold released on 2026-03-29.

## GitHub-ready additions

This scaffold now includes:
- GitHub issue forms
- CI and docs workflows
- Dependabot configuration
- CODEOWNERS, SECURITY, and SUPPORT guides
- a project-board seed file and `gh` seeding helper
- a recommended first commit series for publishing the repo cleanly

See:
- [First Commit Series](docs/FIRST_COMMIT_SERIES.md)
- [Project Board Seed](docs/PROJECT_BOARD_SEED.md)


## Current scaffold status

- FastAPI character scaffold with REST routes and a live WebSocket event stream at `/ws/events`.
- Browser operator console scaffold with live activity updates wired to the stream.
- In-memory event bus, routine triggers, emote triggers, and dialogue test bench for the first vertical slice.

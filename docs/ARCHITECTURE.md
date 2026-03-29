# Architecture

## Overview
This monorepo separates the project into four logical layers:

1. **Runtime core integration**
2. **Sweetie-Bot character layer**
3. **Content and asset layer**
4. **Operations and deployment layer**

## Top-level flow

```mermaid
flowchart TD
    A[User / Crowd / Operator] --> B[Voice + Perception Layer]
    B --> C[Dialogue Manager]
    B --> D[Attention Manager]
    C --> E[Character Director]
    D --> E
    E --> F[Intent / Emote Planner]
    F --> G[Runtime Goal Queue / Behavior Engine]
    F --> H[Speech Planner / TTS]
    G --> I[Safety Layer]
    I --> J[Robot Bridge / Sim Bridge]
    J --> K[Robot Motion]
    H --> L[Speaker + Face/LED + Tail]
    K --> M[Telemetry / State]
    M --> D
    M --> E
    M --> N[Web Interface / Operator Dashboard]
```

## Ownership

### Runtime core
Owns:
- robot motion
- bridge selection
- safety
- plugin lifecycle
- authoritative runtime state

### Sweetie-Bot layer
Owns:
- persona state
- dialogue logic
- attention policies
- routine planning
- memory rules
- expression mapping

### Assets
Owns:
- persona YAML
- phrase banks
- routines
- prompt/style docs
- accessory presets

### Ops
Owns:
- bootstrapping
- deploy profiles
- runbooks
- log replay
- packaging helpers

## Data contracts
See:
- `docs/contracts/EVENTS.md`
- `docs/contracts/API.md`
- `docs/contracts/ASSETS.md`
- `docs/contracts/ROUTINES.md`

## Architectural decisions
See the ADRs in `docs/adr/`.

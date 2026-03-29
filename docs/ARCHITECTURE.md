# Architecture

## Overview

The current scaffold has three layers:

1. **API scaffold** in `upstream_api/`
2. **Reusable character logic** in `sweetiebot/` and `plugins/`
3. **Operator console** in `upstream-web/src/`

The API owns state, transport, and the event bus.
The plugins own character decisions.
The assets repo folder supplies persona, emote, and routine data.

## Runtime flow

```text
HTTP / WebSocket request
        ↓
FastAPI route
        ↓
RuntimeState
        ↓
Sweetie-Bot plugin
        ↓
asset-backed helpers in sweetiebot/
        ↓
event bus + response payload
```

## Why the plugin split matters

The interesting parts of Sweetie-Bot are now easier to reuse:

- persona selection
- dialogue generation
- attention targeting
- emote lookup
- routine metadata

That means a future CERBERUS fork can absorb these pieces without taking the entire prototype runtime along for the ride.

## Current limitations

- no real hardware bridge
- no persistence beyond process memory
- no auth on the scaffold routes
- no actual routine execution engine yet, only routine metadata and selection
- no speech synthesis or speech recognition yet

## Next architectural step

Add a tiny routine planner that can turn routine steps into an ordered list of timed actions for the operator console and, later, the robot runtime.

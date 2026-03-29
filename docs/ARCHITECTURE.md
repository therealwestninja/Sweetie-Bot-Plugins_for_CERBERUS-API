# Architecture

## Intent

Sweetie Bot Fork treats the CERBERUS-facing runtime as the stable control plane and pushes character behavior into reusable plugins.

## Core split

- `upstream_api/` owns state, routes, events, and integration seams
- `plugins/` owns reusable character behavior modules
- `sweetiebot/` owns shared runtime helpers used by those plugins
- `sweetiebot-assets/` owns authorable data files for personas, routines, emotes, and accessories
- `upstream-web/` owns operator and authoring UI scaffolding

## Foundation plugins

### `sweetiebot_persona`
Owns persona profile selection, mood shaping, and persona defaults such as the preferred idle emote and accessory scene.

### `sweetiebot_emotes`
Owns expression selection and translates high-level mood or explicit emote requests into body-profile metadata plus accessory-scene hints.

### `sweetiebot_routines`
Owns routine planning and simple routine start metadata. The current planner produces a previewable step list with estimated timing.

### `sweetiebot_accessories`
Owns accessory scene cataloging and application. In a real CERBERUS integration this plugin would be the boundary between character intent and hardware-specific lighting, tail, display, or audio adapters.

## Why plugin-first

A plugin-first foundation makes the work more reusable for other CERBERUS users. A convention bot, a companion bot, and a demo kiosk may all want the same persona, emote, or accessory logic even if they differ in hardware or UI.

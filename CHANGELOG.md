# Changelog

## 0.0.7 - 2026-03-29
- added configurable dialogue provider adapters for local, OpenAI, and Anthropic backends
- added `GET /character/llm`
- added CERBERUS audio adapter for forwarding spoken replies to onboard Go2 audio endpoints
- expanded `sweetiebot_dialogue` to produce provider and audio metadata
- added `sweetiebot_accessories` plugin description and inventory
- updated websocket snapshot payloads with LLM and audio status
- refreshed README and core docs to read like a real GitHub scaffold

## 0.0.6 - 2026-03-29
- moved more character logic into reusable CERBERUS-style plugins
- added `GET /plugins`
- upgraded routines to load real YAML step data
- upgraded emotes to load JSON asset metadata and accessory hints
- improved dialogue behavior for greetings, music, and praise
- updated the web console to show plugin inventory and richer routine buttons

## 0.0.5 - 2026-03-29
- added persona preset switching end to end

## 0.0.4 - 2026-03-29
- added live event streaming with `GET /events` and `WS /ws/events`

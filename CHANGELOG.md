# Changelog

## 0.0.8

- expanded persona assets to include default emotes, accessory scenes, and routine tags
- moved more of the emote, routine, and accessory groundwork into reusable CERBERUS-style plugins
- added `GET /character/foundation` for authoring-oriented runtime metadata
- added `GET /emotes`
- added `GET /routines/{routine_id}/plan`
- added `GET /accessories/scenes` and `POST /accessories/scene`
- accessory state is now asset-driven rather than a flat boolean-only response
- character state now tracks active emote and active accessory scene
- refreshed README and documentation for the plugin-focused foundation pass

## 0.0.7

- added OpenAI and Anthropic dialogue provider scaffolds
- added configurable CERBERUS onboard audio adapter
- added `/character/llm`
- updated console scaffold with LLM and audio status

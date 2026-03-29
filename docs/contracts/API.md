# API Contract

## Character

- `GET /character` returns current character state
- `GET /character/personas` returns persona profiles
- `GET /character/foundation` returns the active persona profile plus authoring catalogs for emotes, routines, and accessories
- `GET /character/llm` returns dialogue provider and audio sink metadata
- `POST /character/persona` switches personas
- `POST /character/say` produces a spoken reply
- `POST /character/emote` resolves an emote and accessory scene
- `POST /character/routine` starts a routine
- `POST /character/focus` updates attention target
- `POST /character/cancel` clears active speech/routine state

## Emotes

- `GET /emotes` returns the emote catalog

## Routines

- `GET /routines` returns the routine catalog
- `GET /routines/{routine_id}/plan` returns a preview plan with estimated duration and normalized step metadata

## Accessories

- `GET /accessories` returns capabilities, accessory scene catalog, active scene, and audio sink metadata
- `GET /accessories/scenes` returns only the accessory scene catalog
- `POST /accessories/scene` applies an accessory scene by id

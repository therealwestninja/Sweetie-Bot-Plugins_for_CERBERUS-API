# sweetie-plugin-memory-alaya

A reusable memory plugin for Sweetie-Bot / CERBERUS that separates **episodic memory** from **semantic memory**, then retrieves both through a stable API.

## Why this exists

Sweetie-Bot needs to:
- remember what happened
- remember what is true
- forget stale trivia over time
- keep important memories easier to retrieve
- support later consolidation into long-term knowledge

This plugin provides that foundation now, with a lightweight in-process implementation that can later be swapped for a database or vector backend.

## Memory model

### Episodic memory
Use for:
- encounters
- actions taken
- recent observations
- mission outcomes
- interactions with people, animals, places, and objects

### Semantic memory
Use for:
- names
- preferences
- object facts
- map labels
- persistent environment knowledge
- learned rules or summaries

## What it does

- stores episodes and facts
- applies salience scores
- applies time decay
- supports tags and source labels
- retrieves by hybrid score:
  - keyword overlap
  - salience
  - recency
- consolidates repeated episodes into semantic facts

## Supported execute actions

- `memory.store_episode`
- `memory.store_fact`
- `memory.query`
- `memory.consolidate`
- `memory.get`
- `memory.list`
- `memory.delete`
- `memory.status`

## Quick start

### Local
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 7000
```

### Docker
```bash
docker build -t sweetie-plugin-memory-alaya .
docker run --rm -p 7000:7000 --env-file .env.example sweetie-plugin-memory-alaya
```

## Example: store an episode

```bash
curl -X POST http://localhost:7000/execute   -H "Content-Type: application/json"   -d '{
    "type": "memory.store_episode",
    "payload": {
      "text": "Met the operator near the charging dock and followed them to the hallway.",
      "tags": ["operator", "charging_dock", "hallway"],
      "source": "runtime-orchestrator",
      "salience": 0.9
    }
  }'
```

## Example: store a fact

```json
{
  "type": "memory.store_fact",
  "payload": {
    "text": "The charging dock is in the east room.",
    "tags": ["charging_dock", "east_room"],
    "source": "world-model",
    "salience": 0.8
  }
}
```

## Example: query memory

```json
{
  "type": "memory.query",
  "payload": {
    "text": "Where is the charging dock?",
    "limit": 5
  }
}
```

## Example: consolidate

```json
{
  "type": "memory.consolidate",
  "payload": {
    "min_tag_overlap": 2
  }
}
```

## Why this matters

This is one of the most important Sweetie plugins because it gives perception, missions, and AI interaction a shared long-term continuity layer.

It is the foundation for:
- remembering people and their preferences
- remembering object locations
- remembering successful or failed actions
- learning stable facts from repeated experience

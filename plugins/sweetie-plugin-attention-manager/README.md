# sweetie-plugin-attention-manager

A reusable attention and focus-selection layer for Sweetie-Bot.

## Why this exists

Once Sweetie can see and think, she needs to decide what deserves her attention right now.

This plugin helps when there are:
- multiple people in view
- multiple objects of interest
- competing social and environmental signals
- a need to choose one focus target cleanly

## What it does

- ingests candidate targets from perception, cognition, or world-state
- scores them by novelty, salience, social importance, and persistence
- ranks candidate targets
- selects a current focus
- remembers previous attention so the system feels less twitchy

## Supported execute actions

- `attention.ingest_candidates`
- `attention.rank`
- `attention.select_focus`
- `attention.set_bias`
- `attention.get_focus`
- `attention.reset`
- `attention.status`

## Example candidate

```json
{
  "target_id": "person-001",
  "label": "person",
  "confidence": 0.94,
  "tags": ["operator"],
  "distance_m": 1.2,
  "novelty": 0.2,
  "salience": 0.9
}
```

## Why this matters

This makes Sweetie feel more believable:
- she can stay focused on the operator
- she can notice novel things
- she can avoid attention flicker
- she can prioritize social targets over background clutter

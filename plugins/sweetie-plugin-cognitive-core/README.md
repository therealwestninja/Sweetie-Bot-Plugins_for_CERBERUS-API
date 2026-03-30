# sweetie-plugin-cognitive-core

The first real "brain layer" for Sweetie-Bot.

This plugin sits between perception/memory/world-state and the action/runtime stack.

## What it does

- interprets events from perception and other systems
- scores attention targets
- maintains lightweight internal state
- chooses suggested actions
- emits controller/backend-friendly action recommendations
- stores important encounters into memory
- can publish cognitive events to the event bus

## Why this matters

Perception tells Sweetie **what happened**.

Cognitive Core decides:
- whether it matters
- what the current focus should be
- whether to observe, greet, follow, avoid, dock, or ignore
- which named action should be suggested next

Without this layer, the system can see but cannot really decide.

## Supported execute actions

- `cognition.perceive_event`
- `cognition.evaluate_context`
- `cognition.choose_action`
- `cognition.set_state`
- `cognition.get_state`
- `cognition.reset`
- `cognition.status`

## Core behavior model

This plugin currently uses a lightweight rule-based cognitive loop:
- attention scoring
- curiosity weighting
- familiarity/memory lookup
- simple intent selection
- action suggestion via action-registry-compatible envelopes

This is intentional.
It gives Sweetie a usable decision layer now, while leaving room for later upgrades into more advanced planning/reasoning.

## Example: perceive a person-detected event

```json
{
  "type": "cognition.perceive_event",
  "payload": {
    "event": {
      "topic": "vision.person_detected",
      "source": "perception-core",
      "payload": {
        "track_id": "person-001",
        "label": "person",
        "confidence": 0.94,
        "position": {"x": 1.2, "y": 0.3},
        "tags": ["operator"]
      }
    }
  }
}
```

## Example: choose action

```json
{
  "type": "cognition.choose_action",
  "payload": {
    "context": {
      "battery": 0.72,
      "current_goal": null
    }
  }
}
```

## Output style

Responses include:
- interpreted event summary
- attention score
- chosen goal/focus
- suggested next action
- optional action-registry dispatch envelope

## Recommended integrations

Feed it:
- perception events
- world-model summaries
- memory query results
- battery / docking state
- operator commands

Then route output into:
- action registry
- runtime orchestrator
- safety governor
- interaction core

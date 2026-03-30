# sweetie-plugin-safety-governor

Safety policy and action-governing layer for Sweetie-Bot / CERBERUS.

This plugin evaluates proposed actions before they reach runtime or robot control.

## What it does

- checks movement speed against configured limits
- blocks or warns on low-battery risky behavior
- enforces minimum human distance constraints
- supports restricted/no-go zones
- provides emergency-stop state
- returns normalized allow / warn / block decisions

## Why this matters

If Sweetie-Bot is going to safely roam, perceive, and interact, every meaningful action needs a safety layer between cognition and execution.

This plugin is designed to sit here:

Perception -> Cognition -> Safety Governor -> Action Registry / Runtime -> Robot

## Supported execute actions

- `safety.evaluate_action`
- `safety.set_policy`
- `safety.get_policy`
- `safety.report_context`
- `safety.estop`
- `safety.clear_estop`
- `safety.status`

## Example evaluate request

```json
{
  "type": "safety.evaluate_action",
  "payload": {
    "action": {
      "type": "runtime.follow_object",
      "payload": {
        "object_id": "person-001",
        "speed_mps": 1.6,
        "target_distance_m": 0.4,
        "position": {"x": 2.1, "y": 1.0}
      }
    },
    "context": {
      "battery": 0.18,
      "nearest_human_distance_m": 0.55
    }
  }
}
```

## Decision model

The plugin returns:
- `decision`: `allow`, `warn`, or `block`
- `reasons`
- `normalized_action`
- `safety_flags`

This makes it easy for the controller or backend to show the result to the operator and decide whether to proceed.

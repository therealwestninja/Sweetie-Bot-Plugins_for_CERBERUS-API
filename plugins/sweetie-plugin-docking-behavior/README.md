# sweetie-plugin-docking-behavior

A reusable docking behavior layer for Sweetie-Bot.

## What it does

- stores Sweetie's known dock location
- decides when docking should be prioritized
- plans a safe approach to the dock
- returns alignment instructions for final positioning
- transitions into a charging state

## Why this matters

Sweetie now has:
- spatial memory
- navigation
- safety
- cognition

This plugin turns those layers into a practical autonomous behavior:
- notice low battery
- seek dock
- approach dock
- align carefully
- begin charging

## Supported execute actions

- `docking.set_dock`
- `docking.seek_dock`
- `docking.plan_approach`
- `docking.align`
- `docking.begin_charge`
- `docking.get_state`
- `docking.reset`
- `docking.status`

## Example input

```json
{
  "type": "docking.seek_dock",
  "payload": {
    "battery": 0.16,
    "current_position": {"x": 0.0, "y": 0.0}
  }
}
```

## Example output

```json
{
  "should_dock": true,
  "reason": "battery_low",
  "dock_target": {"x": 2.1, "y": -0.5},
  "suggested_action": {
    "type": "navigation.plan_to_point",
    "payload": {
      "goal": {"x": 2.1, "y": -0.5}
    }
  }
}
```

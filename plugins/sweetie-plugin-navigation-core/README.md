# sweetie-plugin-navigation-core

A goal-directed navigation layer for Sweetie-Bot.

## What it does

- keeps track of Sweetie's current position
- plans routes to points or remembered locations
- returns simple step-based waypoints
- tracks active routes
- supports route cancelation and route inspection

## Why this matters

This is the layer that lets Sweetie do more than react.
She can now:
- go to a remembered place
- travel to a target point
- follow a generated route
- connect spatial memory to motion planning

## Supported execute actions

- `navigation.set_position`
- `navigation.plan_to_point`
- `navigation.plan_to_location`
- `navigation.follow_route`
- `navigation.cancel_route`
- `navigation.get_route`
- `navigation.status`

## Example

```json
{
  "type": "navigation.plan_to_point",
  "payload": {
    "goal": {"x": 3.0, "y": 1.5}
  }
}
```

## Example using a named location

```json
{
  "type": "navigation.plan_to_location",
  "payload": {
    "name": "charging_dock",
    "locations": {
      "charging_dock": {"x": 2.1, "y": -0.5}
    }
  }
}
```

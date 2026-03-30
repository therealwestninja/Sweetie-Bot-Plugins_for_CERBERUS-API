# sweetie-plugin-runtime-orchestrator

A controller-friendly orchestration layer that chains multiple Sweetie plugins together behind one stable endpoint.

This plugin is the next step after building individual plugins:
- it keeps the CERBERUS controller simple
- it composes multi-plugin flows
- it centralizes higher-level routines without hardcoding them into every service

## What it does

It provides reusable chain-level actions such as:
- `runtime.chain_execute` — execute a named sequence of plugin calls
- `runtime.follow_object` — use world-model + nav to pursue a known semantic object
- `runtime.patrol_mission` — build and trigger a mission from waypoint input
- `runtime.simulate_chain` — record a multi-step orchestration into sim-learn
- `runtime.register_routes` — expose known integration targets
- `runtime.status` — inspect configured integration endpoints and last chain results

## Why this matters

Without an orchestrator:
- the controller must manually coordinate multiple plugins
- backend logic sprawls across services
- cross-plugin behaviors are harder to test

With an orchestrator:
- the controller can call one higher-level action
- plugin composition becomes reusable
- future runtime/event-bus work has a stable stepping stone

## Example: follow a known object

```json
{
  "type": "runtime.follow_object",
  "payload": {
    "object_id": "person-001",
    "standoff_m": 0.75
  }
}
```

This will:
1. query the world model for the object
2. derive a goal position
3. emit a `nav.goal` request envelope

## Example: patrol mission

```json
{
  "type": "runtime.patrol_mission",
  "payload": {
    "waypoints": [
      {"x": 0, "y": 0},
      {"x": 2, "y": 0},
      {"x": 2, "y": 2}
    ],
    "loop": true
  }
}
```

This will:
1. normalize the waypoint route
2. build a mission tree
3. return a ready-to-send mission payload

## Example: simulate a chain

```json
{
  "type": "runtime.simulate_chain",
  "payload": {
    "episode_name": "follow-person-demo",
    "steps": [
      {
        "observation": {"person_seen": true},
        "action": {"type": "runtime.follow_object", "payload": {"object_id": "person-001"}},
        "reward": 0.6
      }
    ]
  }
}
```

## Notes

This plugin currently returns normalized requests and chain results while optionally calling live plugin endpoints if they are available.

That makes it useful now, while still being safe for staged integration.

# sweetie-plugin-action-registry

A reusable action registry and dispatch layer for Sweetie-Bot / CERBERUS.

This plugin gives the ecosystem a stable place to define:
- named actions
- target handlers
- adapters
- execution policy
- controller-safe routing metadata

## Why this exists

As the plugin ecosystem grows, the system needs more than raw capability calls.
It needs a reusable way to say:

- "follow_operator" means this specific action chain
- "dock_now" should route through a preferred adapter
- "speak_polite" is allowed, but only through specific handlers
- "high_speed_run" requires a stricter policy level

Without an action registry:
- action names drift
- routing logic gets duplicated
- controller presets become brittle
- policy checks become inconsistent

With an action registry:
- named actions become first-class
- multiple adapters can expose the same action
- dispatch results can be normalized
- future policy and dependency injection become much easier

## Supported execute actions

- `action.register`
- `action.unregister`
- `action.list`
- `action.get`
- `action.dispatch`
- `action.set_policy`
- `action.status`

## Action model

Each action registration includes:
- `action_name`
- `description`
- `handler_type`
- `target_plugin`
- `target_action`
- optional tags
- optional policy

Example:

```json
{
  "type": "action.register",
  "payload": {
    "action_name": "follow_operator",
    "description": "Follow the known operator target.",
    "handler_type": "plugin_execute",
    "target_plugin": "runtime-orchestrator",
    "target_action": "runtime.follow_object",
    "default_payload": {"object_id": "operator-001", "standoff_m": 0.8},
    "tags": ["follow", "person"],
    "policy": {"safety_level": "normal"}
  }
}
```

## Dispatch result

Dispatch returns a normalized envelope that downstream runtimes or controller code can execute directly.

This plugin is intentionally safe-by-default:
it does not force live cross-plugin execution to exist in order to be useful.
It can act as the canonical source of truth for action definitions now, and later become the live dispatch core.

## Why this matters

This is the first real step toward:
- dispatcher-centric architecture
- adapter separation
- cleaner orchestration
- reusable named behaviors
- safer action policy enforcement

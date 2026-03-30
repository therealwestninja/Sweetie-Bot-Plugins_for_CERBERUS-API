# sweetie-plugin-gait-library

A reusable gait-profile plugin for Sweetie-Bot / CERBERUS.

This plugin lets the platform treat **movement style** as a selectable, reusable control layer instead of hardcoding one default quadruped behavior.

## Why this matters

The Unitree GO2 is naturally used like a canine-style quadruped, but there is no reason the controller has to stay locked to one expressive locomotion profile.

This plugin adds a stable way to request:
- canine / default quadruped movement
- equine-inspired movement profiles
- breed/style-specific ambling or pacing modes
- controller-friendly gait adaptation without changing the controller contract every time

## What it does

It provides:
- gait profile catalog
- named gait definitions
- active gait selection
- command adaptation
- preview sequences

The adaptation layer turns a high-level movement request into a normalized envelope that downstream motion plugins or the CERBERUS API can interpret.

## Supported execute actions

- `gait.list_profiles`
- `gait.list_gaits`
- `gait.get_gait`
- `gait.set_active`
- `gait.get_active`
- `gait.adapt_command`
- `gait.preview_sequence`
- `gait.status`

## Included profiles

### Canine / default quadruped
- walk
- trot
- canter
- gallop
- pace

### Equine-inspired
- walk
- trot
- canter
- gallop
- tölt
- flying_pace
- marcha_picada
- running_walk

## Notes on gait references

This plugin uses commonly described gait patterns:
- walk as a four-beat gait
- trot as a two-beat diagonal gait
- canter as a three-beat gait
- gallop as a faster four-beat gait
- Icelandic horses are commonly described as having walk, trot, canter, tölt, and pace
- the running walk is a four-beat gait associated with Tennessee Walking Horses

## Example: select the equine profile

```bash
curl -X POST http://localhost:7000/execute   -H "Content-Type: application/json"   -d '{
    "type": "gait.set_active",
    "payload": {
      "profile": "equine",
      "gait": "tolt"
    }
  }'
```

## Example: adapt a move request

```json
{
  "type": "gait.adapt_command",
  "payload": {
    "command": {
      "type": "robot.command",
      "payload": {
        "action": "move",
        "speed_mps": 0.8,
        "direction": "forward",
        "duration_s": 3.0
      }
    }
  }
}
```

Response includes:
- active gait metadata
- normalized movement style parameters
- recommended cadence, duty factor, bounce, and body-carriage hints
- adapted command envelope for downstream plugins

## Why this is useful now

Even before deep low-level gait synthesis exists, this plugin gives the ecosystem:
- stable gait naming
- reusable movement styles
- controller presets
- a hook for future motion adaptation

That means plugins can request **"equine.tolt"** or **"canine.trot"** today, and the motion backend can learn how to honor that over time.

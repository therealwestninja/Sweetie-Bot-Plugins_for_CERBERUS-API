# sweetie-plugin-behavior-engine

A personality-driven behavior layer for Sweetie-Bot.

This plugin is tuned around a Sweetie Belle-inspired interaction style:
- kind
- emotional
- creative
- enthusiastic
- affectionate
- curious
- wholesome
- occasionally dramatic in a cute way

## What it does

It takes high-level intents from cognition / interaction and turns them into:
- styled behavior modes
- tone
- speech suggestions
- movement style hints
- attention bias hints
- character-consistent action envelopes

## Why this matters

Without a behavior layer:
- the robot can decide what to do
- but not how to do it in-character

With this plugin:
- Sweetie can greet warmly
- follow in an excited, playful way
- react with curiosity
- encourage others
- sound youthful and expressive
- remain wholesome and supportive

## Supported execute actions

- `behavior.process_intent`
- `behavior.generate_style`
- `behavior.set_persona_state`
- `behavior.get_persona_state`
- `behavior.reset`
- `behavior.status`

## Example input

```json
{
  "type": "behavior.process_intent",
  "payload": {
    "intent": "engage_operator",
    "context": {
      "target_id": "person-001",
      "is_operator": true,
      "battery": 0.78
    }
  }
}
```

## Example output

```json
{
  "behavior_mode": "excited_follow",
  "tone": "bright_cheerful",
  "speech": "Ooo! There you are! I'll come with you!",
  "movement_style": "light_trot",
  "attention_bias": "operator_locked"
}
```

## Character target

This plugin is designed around a Sweetie Belle-like target personality:
- energetic, friendly, affectionate, curious, adventurous, dramatic, loyal, creative
- bright, expressive, youthful tone
- short enthusiastic speech
- wholesome and playful behavior
- excited kid-discovering-the-world vibe

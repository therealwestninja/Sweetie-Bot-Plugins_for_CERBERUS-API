# Routine Contracts

## Step types
- say
- emote
- wait
- accessory
- focus
- marker

## Example
```yaml
id: greeting_01
steps:
  - type: focus
    target: nearest_person
  - type: emote
    id: curious_headtilt
  - type: say
    text_key: greetings.default_01
```

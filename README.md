# 🤖 Sweetie-Bot for CERBERUS API

**Sweetie-Bot** is a character-driven AI runtime designed to operate as a **high-level behavioral controller** for robotic systems via the **CERBERUS API**, with a focus on expressive, reactive, personality-based interaction.

It is designed to run alongside the **Companion Web Interface** and control physical systems such as the **Unitree GO2**.

---

# 🚀 Current Status

**Version:** Early Integration (Post-Scaffold)
**State:** Functional vertical slice complete

✅ Canonical API defined
✅ WebSocket event system implemented
✅ Nudge-based interaction model working
✅ Companion Web Interface integration working
✅ CERBERUS adapter (stub) implemented
⚠️ Hardware execution still stubbed (next phase)

---

# 🧠 Core Concept

Sweetie-Bot is NOT a direct command system.

Instead, it uses a **“nudge → reaction → decision → execution”** loop:

1. UI sends a *nudge* (intent)
2. Sweetie-Bot generates a reaction
3. System decides what action to take
4. Action is passed to CERBERUS
5. Result is streamed back to UI

---

# 🏗 Architecture Overview

```
Companion Web UI
        ↓
POST /character/nudge
        ↓
Sweetie-Bot Runtime
  - Persona
  - Mood
  - Decision logic
        ↓
WebSocket (/ws/events)
        ↓
CERBERUS Adapter (stub → real hardware)
        ↓
Execution Ack → UI
```

---

# 📡 Canonical API

### Base URL

```
http://localhost:8000
```

---

## 🔹 State Endpoints

### `GET /character`

Returns current character state

### `GET /accessories`

Returns available accessory scenes

### `GET /memory/summary`

Returns memory snapshot

---

## 🔹 Interaction

### `POST /character/nudge`

Primary interaction endpoint.

#### Example:

```json
{
  "intent": "greet"
}
```

#### Response:

```json
{
  "reaction": {
    "speech": "Oh! Hello there~!",
    "emote": "happy",
    "attention": "user",
    "intensity": 0.8
  },
  "decision": {
    "action_type": "emote",
    "action_id": "greet",
    "parameters": {}
  }
}
```

---

## 🔹 Streaming

### `WS /ws/events`

All real-time state updates are streamed here.

---

### Event Format

```json
{
  "type": "string",
  "source": "system|character|cerberus",
  "schema_version": "1.0",
  "replay_safe": false,
  "payload": {}
}
```

---

### Event Types

* `events.snapshot` (initial state)
* `character.nudge_reaction`
* `cerberus.execution_ack`

---

# ⚙️ Installation

## Requirements

* Python 3.10+
* pip
* (Optional) virtualenv

---

## Install

```bash
git clone https://github.com/therealwestninja/Sweetie-Bot_for_CERBERUS-API
cd Sweetie-Bot_for_CERBERUS-API

pip install -e .
```

---

## Run

```bash
uvicorn sweetiebot.api.app:create_app --reload
```

---

Server runs at:

```
http://localhost:8000
```

---

# 🌐 Companion Web Interface Setup

In the Companion Web Interface repo:

* Connect to:

```
ws://localhost:8000/ws/events
```

* Send interactions via:

```
POST /character/nudge
```

---

## Example UI Actions

| Action       | Intent    |
| ------------ | --------- |
| Greet Guest  | `greet`   |
| Idle         | `idle`    |
| Perk Up      | `perk_up` |
| Focus Target | `focus`   |

---

# 🤖 CERBERUS Integration

Currently implemented as a **stub adapter**:

```python
send_to_cerberus(action)
```

### Current behavior:

* Simulates execution
* Returns success/failure
* Emits websocket event

---

## Next Phase (Planned)

* Real GO2 motion mapping
* Audio output pipeline
* Capability negotiation
* Safety gating

---

# 🧪 Testing

Run tests:

```bash
pytest
```

---

### Current Coverage

* API endpoints
* WebSocket snapshot + events
* Nudge → reaction flow
* Execution acknowledgment

---

# 📁 Project Structure

```
sweetiebot/
  api/
    app.py              # Canonical API entrypoint
    nudge_patch.py      # Nudge + websocket integration
  runtime/
    events.py           # Event bus
    execution.py        # Action pipeline
    cerberus_adapter.py # Hardware bridge (stub)

docs/
tests/
upstream_api/           # Legacy compatibility shim
```

---

# ⚠️ Important Notes

* `sweetiebot.api.app:create_app()` is the **ONLY supported entrypoint**
* `upstream_api/` exists for backward compatibility only
* Direct control endpoints (emote/routine) are being deprecated
* Web UI should ONLY use `/character/nudge`

---

# 🧭 Roadmap

## Near-Term

* Replace stub CERBERUS adapter with real hardware control
* Expand reaction/decision logic
* Asset-driven emotes and routines

## Mid-Term

* Perception system (vision/audio)
* Personality tuning + memory persistence
* Multi-character support

## Long-Term

* Fully autonomous behavioral agent
* Multi-device orchestration
* Real-time interactive robotics personality system

---

# 🤝 Contributing

This project is evolving rapidly.

If contributing:

* Follow the canonical API design
* Do NOT introduce direct control shortcuts
* Maintain event-driven architecture

---

# 📜 License

TBD

---

# 💡 Summary

This is no longer a scaffold.

This repo now provides:

* A **real-time character runtime**
* A **stable API surface**
* A **working UI → AI → execution loop**

The next step is **hardware reality**.

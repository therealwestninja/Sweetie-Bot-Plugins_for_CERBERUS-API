# REAL HARDWARE STATUS — Sweetie-Bot for CERBERUS / Unitree GO2

Last updated: 2026-03

This document tracks what is **implemented**, **stubbed**, **simulated**, or
**unsafe for live hardware**.  Check this before deploying to a real GO2.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ REAL | Implemented and tested in production |
| 🔶 PARTIAL | Partially implemented — needs hardware validation |
| 🔷 SIMULATED | Runs in software; real hardware path not exercised |
| ❌ STUB | Placeholder only — will not work on hardware |
| 🚫 UNSAFE | Do not use on live hardware without review |

---

## Component Status

### Runtime & API

| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI app (`sweetiebot.api.app`) | ✅ REAL | Boots, routes work, tested |
| Plugin registry | ✅ REAL | All builtins registered and health-checked |
| Character state manager | ✅ REAL | Mood, memory, focus all functional |
| WebSocket event stream | ✅ REAL | Pub/sub hub, keepalive, snapshot |
| `/character/respond` → `CharacterResponse` | ✅ REAL | Typed Pydantic v2 schema |
| `/integration/plan` | ✅ REAL | Gate → mapper → plan pipeline |
| `/integration/validate` | ✅ REAL | Stateless pre-flight |
| `/debug/last-decision` | ✅ REAL | Decision ledger |

### Adapter Layer

| Component | Status | Notes |
|-----------|--------|-------|
| `UnitreeGo2Adapter` — simulation mode | ✅ REAL | Logs commands, no SDK needed |
| `UnitreeGo2Adapter` — real SDK mode | 🔷 SIMULATED | SDK path exists but untested on hardware |
| Connection lifecycle (`connect/disconnect/reconnect`) | 🔶 PARTIAL | Implemented; needs hardware test |
| Motion execution (`execute_motion`) | 🔷 SIMULATED | Calls SDK stub; not hardware-validated |
| Audio playback (`play_audio`) | 🔷 SIMULATED | Stub only |
| Accessory state (`set_accessory_state`) | 🔷 SIMULATED | Stub only |
| Health check + capability reporting | ✅ REAL | Works in sim; maps to real SDK |
| Emergency stop | ✅ REAL | Implemented in adapter and safety gate |

### Safety

| Component | Status | Notes |
|-----------|--------|-------|
| Allowlist-based CERBERUS mapper | ✅ REAL | Fail-closed, unknown IDs rejected |
| Safety gate (NORMAL/SAFE/DEGRADED/EMERGENCY) | ✅ REAL | Per-routine cooldowns, mode blocking |
| Rate limiting (token bucket per routine_id) | ✅ REAL | Configurable per-routine cooldowns |
| Operator override | ✅ REAL | Flag-based, bypasses rate limits |
| Emergency stop handling | ✅ REAL | In safety gate + adapter |
| Motion preconditions | 🔶 PARTIAL | Basic; needs hardware-specific expansion |
| Repetition suppression | 🔶 PARTIAL | Cooldowns exist; semantic suppression TBD |

### Dialogue

| Component | Status | Notes |
|-----------|--------|-------|
| Rule-based dialogue (fallback) | ✅ REAL | Keyword matching, always works |
| Structured dialogue provider | ✅ REAL | Typed output `{speech,emotion,intent,...}` |
| LLM dialogue provider (OpenAI/Anthropic) | 🔷 SIMULATED | HTTP client exists; needs API key |
| Memory context feedback loop | ✅ REAL | Recent memory injected into dialogue |
| Safety output filtering | ✅ REAL | All dialogue output routed through gate |

### Expression Coordination

| Component | Status | Notes |
|-----------|--------|-------|
| `ExpressionCoordinator` | ✅ REAL | Speech + motion + emote + accessory coordination |
| Overlap prevention | ✅ REAL | Locks prevent concurrent motion commands |
| Interruption handling | ✅ REAL | Cancel-and-replace semantics |
| Neutral recovery on failure | ✅ REAL | Returns to neutral on any error |

### Event / Perception Pipeline

| Component | Status | Notes |
|-----------|--------|-------|
| `EventPipeline` — ingestion | ✅ REAL | Normalized schema, async-safe |
| `user_input` events | ✅ REAL | |
| `person_detected` events | ✅ REAL | Updates focus target |
| `proximity_alert` events | ✅ REAL | Triggers safe mode |
| `system_fault` events | ✅ REAL | Triggers degraded/emergency |
| `battery_low` events | ✅ REAL | Triggers degraded mode |
| `speech_transcript` events | 🔷 SIMULATED | Schema exists; no real STT yet |
| Real sensor integration (lidar, camera) | ❌ STUB | Not implemented |

---

## Hardware Deployment Checklist

Before deploying to a real Unitree GO2:

- [ ] Set `SWEETIEBOT_SIM_MODE=0` in environment
- [ ] Verify Unitree SDK is installed and accessible
- [ ] Set network interface for CycloneDDS (`UNITREE_ETHERNET`)
- [ ] Run `GET /health` and confirm all plugins healthy
- [ ] Run `GET /integration/capabilities` and confirm allowlist matches robot capabilities
- [ ] Confirm safety gate is in NORMAL mode
- [ ] Test emergency stop: `POST /integration/safety/mode {"mode": "emergency"}`
- [ ] Confirm `return_to_neutral` routine executes correctly
- [ ] Run full test suite: `pytest -q`

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SWEETIEBOT_SIM_MODE` | `1` | `1` = simulation, `0` = real hardware |
| `SWEETIEBOT_ADAPTER` | `unitree_go2` | Adapter to use |
| `UNITREE_ETHERNET` | `eth0` | Network interface for GO2 connection |
| `SWEETIEBOT_LOG_LEVEL` | `INFO` | Logging verbosity |
| `OPENAI_API_KEY` | — | For LLM dialogue provider |
| `ANTHROPIC_API_KEY` | — | For LLM dialogue provider |

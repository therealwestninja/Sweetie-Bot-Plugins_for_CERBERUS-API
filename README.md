# Sweetie Bot (CERBERUS API Framework)

## Status
Sweetie Bot is currently in **Framework Expansion Phase**.

The system now includes:
- Plugin architecture (discoverable, configurable)
- Dialogue + persona + routine systems
- Runtime orchestration layer
- Safety policy plugin
- API endpoints

## What’s Next (Ordered by Ease → Difficulty)

### 🟢 EASY (Immediate Wins)
- Unify versioning across README, pyproject, changelog
- Expand plugin documentation (manifest, lifecycle, examples)
- Add logging + debug output hooks
- Improve error messages and validation reporting
- Add CLI tools for:
  - validating assets
  - listing plugins
  - testing dialogue responses

### 🟡 LOW–MEDIUM COMPLEXITY
- Memory plugin family (SQLite backend)
- CharacterStateManager
- Session memory + short-term memory
- Basic MoodEngine (simple state machine)
- Routine cooldown + interrupt system improvements
- Speech/TTS plugin interface (mock + local)
- Audio output abstraction layer

### 🟠 MEDIUM COMPLEXITY
- BehaviorDirector (decision arbitration layer)
- Attention system plugin
- Perception schema + mock perception plugin
- WorldState aggregator
- Plugin health monitoring + status reporting
- CERBERUS adapter (mock implementation)
- Safety policy expansion (context-aware rules)

### 🔴 HIGH COMPLEXITY
- Persistent multi-layer memory (episodic + semantic)
- Real perception integration (camera, audio)
- Full speech pipeline (queueing, interruption, caching)
- Operator control dashboard (web UI)
- Observability system (tracing + analytics)
- Multi-user interaction model
- Emotion simulation system (dynamic + decay)

### 🔥 VERY HIGH COMPLEXITY (LONG TERM)
- Advanced planning system (goal stacks)
- Autonomous behavior orchestration
- Full CERBERUS integration (real hardware)
- Asset authoring tools (UI editors)
- Plugin marketplace / packaging ecosystem
- Long-session stability + scaling
- Character consistency enforcement system
- Production deployment tooling (Docker, env configs, migrations)

## Design Principle

Sweetie Bot is:
- A **character runtime**
- Not a direct robot controller
- Not an unconstrained AI agent

All outputs must remain:
- bounded
- safe
- interruptible
- observable

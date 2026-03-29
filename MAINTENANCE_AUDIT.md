# Maintenance Audit

## Clean-up applied
- Fixed the broken FastAPI app entrypoint in `sweetiebot/api/app.py`.
- Restored websocket snapshot emission and canonical nudge → ack flow.
- Unified `/character/nudge` so it supports both the legacy nudge handler contract and the first-slice canonical `intent/context` contract.
- Removed stale root-level duplicate source trees that shadowed the packaged `sweetiebot/` code.
- Removed cache/build artifacts and accidental `* (2).py` duplicates.
- Removed obsolete `sweetiebot/api/nudge_patch.py` merge artifact.

## Repo shape after clean-up
The canonical Python package is now the `sweetiebot/` tree defined by `pyproject.toml`.

## Suggested next robotics improvements
1. Add a controller-intent arbitration layer so joystick/button input becomes high-level intents (`acknowledge`, `follow`, `hold`, `pose`, `return_neutral`) instead of direct motion calls.
2. Add a teleop safety envelope that rate-limits mode changes and blocks controller actions while the safety gate is elevated.
3. Add an autonomy blend state machine with explicit modes: `autonomous`, `assistive`, `teleop_override`, `safe_hold`.
4. Add confidence-weighted attention fusion: vision/perception + controller focus cues + dialogue context should compete for `focus_target`.
5. Add a low-latency expression path for controller inputs so bumpers/triggers can request safe emotes/accessory changes without interrupting locomotion.
6. Add execution receipts from CERBERUS back into Sweetie-Bot state so failed motions change dialogue and behavior selection in real time.
7. Add gait/motion cooldown classes, not just per-routine cooldowns, so semantically similar motions do not thrash the robot.
8. Add battery/thermal/fault-aware behavior degradation so autonomy gracefully shifts from playful to conservative before emergency mode.

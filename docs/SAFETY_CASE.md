# Safety Case

## Purpose
This document describes the intended safety posture of the project.

## Safety principles
1. Safety overrides all character behavior.
2. High-level character commands must not bypass runtime controls.
3. Routines must remain interruptible.
4. Perception uncertainty must degrade gracefully.
5. Public-demo behaviors require stricter limits than lab tests.

## Planned controls
- operator soft-stop
- operator hard-stop / emergency stop integration
- stage-safe movement profiles
- proximity-based motion limiting
- safe neutral fallback pose
- degraded mode when sensors or bridges fail

## Out of scope for 0.0.1
This scaffold does not implement safety-critical controls.
It only defines where those controls should live and how they should be documented.

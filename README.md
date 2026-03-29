# Sweetie Bot Patch Bundle v5

This bundle targets the easiest near-term engineering tasks first:

## Added
- Structured JSON event logging
- Unified exception classes
- CLI tooling for:
  - listing plugins
  - validating persona files
  - validating routine files
  - generating test dialogue
- Stronger validation wrappers for persona and routine YAML files
- Runtime logging hooks for:
  - plugin loading
  - dialogue generation
  - validation failures
  - state changes

## Suggested merge targets
- `sweetiebot/observability/`
- `sweetiebot/cli/`
- `sweetiebot/errors.py`
- `sweetiebot/persona/loader.py`
- `sweetiebot/routines/registry.py`
- `sweetiebot/runtime.py`
- `tests/test_cli_and_validation.py`

## Notes
This patch is designed as a drop-in bundle for manual merge into the existing repo.

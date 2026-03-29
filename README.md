# Sweetie Bot Patch Bundle v7

This patch bundle continues the easier production-readiness tasks by adding:

- API endpoints for plugin health/status inspection
- API endpoint for mock speech testing
- CLI commands for plugin/system health inspection
- Example YAML config for TTS/audio plugins
- Documentation for speech plugin config shape

## Included files

- `sweetiebot/api/app.py`
- `sweetiebot/cli/main.py`
- `sweetiebot/runtime.py`
- `sweetiebot/plugins/health.py`
- `docs/PLUGIN_CONFIG_EXAMPLES.md`
- `config/examples/plugins.speech.example.yaml`
- `tests/test_api_health_and_speech.py`
- `tests/test_cli_health.py`

## Notes

This is a patch-style bundle meant to be extracted into the repo root and merged with the existing project.

The changes assume the prior plugin work already exists:
- plugin registry
- plugin health helpers
- mock speech plugins
- runtime plugin bootstrapping

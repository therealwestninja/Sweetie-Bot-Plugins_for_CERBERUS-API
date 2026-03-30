# Plugin test suite

This repository now includes a root-level pytest harness focused on Sweetie plugin contract mapping, endpoint discovery, functional smoke coverage, concurrency stress, fuzzing, and basic security regression checks.

## What it covers

- **Manifest validation**
  - Verifies every `plugins/*/plugin.yaml` file is readable and advertises at least one capability.
  - Confirms plugin names are unique.
  - Checks that declared entrypoints match live FastAPI routes when an app is present.

- **Inpoints / exitpoints / calls / commands mapping**
  - `scripts/map_plugin_contracts.py` walks the plugin tree and emits a JSON report of:
    - manifest metadata
    - declared capabilities
    - discovered HTTP routes
    - action strings seen in code comparisons
  - This is meant to make plugin command surfaces auditable before wiring them into the controller/runtime stack.

- **Functional smoke tests**
  - Health checks for every FastAPI plugin.
  - Execute-path probes for every plugin.
  - Representative valid command payloads for each plugin family.
  - Unknown-action and malformed-request handling.

- **Concurrency / race-condition pressure**
  - Parallel request floods against the most stateful plugins:
    - event bus
    - memory alaya
    - world model
    - payload bus
  - A dedicated publish/subscribe/poll parallel scenario for the event bus.

- **Security / fuzzing**
  - Common abuse strings including traversal, script injection, and oversized string probes.
  - Hypothesis-driven JSON fuzzing to ensure handlers reject bad inputs cleanly instead of crashing.

- **Performance guardrails**
  - Health endpoint latency budget.
  - Small execute-call batch timing budget for locally-computable plugins.

## Running the suite

Install the dev dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run everything:

```bash
pytest
```

Run only one category:

```bash
pytest -m smoke
pytest -m contract
pytest -m security
pytest -m concurrency
pytest -m performance
```

Generate the contract map report:

```bash
python scripts/map_plugin_contracts.py > plugin-contract-map.json
```

## Notes

- Some plugins are simple pass-through stubs. The suite still verifies that they do not crash and that their public interfaces remain stable.
- Plugins with external HTTP dependencies are isolated in tests with local test doubles so the suite can run offline and deterministically.
- Python services are not the place where classic native memory corruption is most likely, but the fuzz and abuse tests are still useful for surfacing parser crashes, unbounded payload handling, serialization blowups, and exception leaks.

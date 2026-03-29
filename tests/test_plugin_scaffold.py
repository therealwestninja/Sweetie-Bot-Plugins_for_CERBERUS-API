from fastapi.testclient import TestClient

from upstream_api.app.main import app

client = TestClient(app)


def test_plugins_endpoint_lists_reusable_plugins() -> None:
    response = client.get('/plugins')
    assert response.status_code == 200
    items = response.json()['items']
    names = {item['name'] for item in items}
    assert {
        'sweetiebot_persona',
        'sweetiebot_dialogue',
        'sweetiebot_routines',
        'sweetiebot_accessories',
    } <= names


def test_routines_include_step_metadata() -> None:
    response = client.get('/routines')
    assert response.status_code == 200
    items = response.json()['items']
    greeting = next(item for item in items if item['id'] == 'greeting_01')
    assert greeting['title'] == 'Greeting 01'
    assert greeting['steps'][0]['type'] == 'focus'

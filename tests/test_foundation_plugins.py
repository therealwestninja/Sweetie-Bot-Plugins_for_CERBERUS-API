from fastapi.testclient import TestClient

from upstream_api.app.main import app

client = TestClient(app)


def test_foundation_endpoint_exposes_authoring_catalogs() -> None:
    response = client.get('/character/foundation')
    assert response.status_code == 200
    payload = response.json()
    assert payload['profile']['id'] in {
        'sweetiebot_default',
        'sweetiebot_convention',
        'sweetiebot_companion',
    }
    assert any(item['id'] == 'curious_headtilt' for item in payload['available_emotes'])
    assert any(item['id'] == 'greeting_01' for item in payload['available_routines'])
    assert any(item['id'] == 'eyes_curious' for item in payload['available_accessory_scenes'])


def test_emote_endpoint_applies_accessory_scene() -> None:
    response = client.post('/character/emote', json={'emote_id': 'curious_headtilt'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['emote_id'] == 'curious_headtilt'
    assert payload['accessory_scene']['scene_id'] == 'eyes_curious'
    assert payload['character']['active_accessory_scene'] == 'eyes_curious'


def test_routine_plan_endpoint_returns_preview_data() -> None:
    response = client.get('/routines/greeting_01/plan')
    assert response.status_code == 200
    payload = response.json()
    assert payload['routine_id'] == 'greeting_01'
    assert payload['step_count'] == 3
    assert payload['estimated_duration_ms'] >= 3000
    assert payload['steps'][0]['step_index'] == 1


def test_accessory_scene_roundtrip() -> None:
    response = client.post('/accessories/scene', json={'scene_id': 'eyes_happy'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['scene_id'] == 'eyes_happy'

    scenes = client.get('/accessories/scenes')
    assert scenes.status_code == 200
    assert any(item['id'] == 'eyes_happy' for item in scenes.json()['items'])

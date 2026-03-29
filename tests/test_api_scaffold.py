from fastapi.testclient import TestClient

from upstream_api.app.main import app

client = TestClient(app)


def test_root_and_character_state() -> None:
    response = client.get('/')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'scaffold-online'
    assert payload['character']['persona_id'] == 'sweetiebot_default'


def test_say_updates_mood_and_returns_reply() -> None:
    response = client.post('/character/say', json={'text': 'hello sweetie bot'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['intent'] == 'greet'
    assert payload['emote_id'] == 'curious_headtilt'
    assert payload['provider'] == 'local'
    assert payload['audio']['sink'] in {'disabled', 'cerberus_go2_onboard_audio'}


def test_persona_list_and_switch_flow() -> None:
    personas = client.get('/character/personas')
    assert personas.status_code == 200
    assert any(item['id'] == 'sweetiebot_convention' for item in personas.json()['items'])

    switched = client.post('/character/persona', json={'persona_id': 'sweetiebot_convention'})
    assert switched.status_code == 200
    payload = switched.json()
    assert payload['character']['persona_id'] == 'sweetiebot_convention'
    assert payload['character']['mood'] == 'excited'

    greeting = client.post('/character/say', json={'text': 'hello'})
    assert greeting.status_code == 200
    assert 'sparkle' in greeting.json()['reply'].lower()


def test_llm_status_endpoint() -> None:
    response = client.get('/character/llm')
    assert response.status_code == 200
    payload = response.json()
    assert payload['provider'] == 'local'
    assert 'audio' in payload


def test_routine_and_cancel_flow() -> None:
    response = client.post('/character/routine', json={'routine_id': 'greeting_01'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['active'] == 'greeting_01'
    assert payload['step_count'] == 3

    cancel = client.post('/character/cancel')
    assert cancel.status_code == 200
    assert cancel.json()['active_routine'] is None


def test_events_endpoint_and_websocket_stream() -> None:
    events_before = client.get('/events')
    assert events_before.status_code == 200
    assert 'items' in events_before.json()

    with client.websocket_connect('/ws/events') as websocket:
        snapshot = websocket.receive_json()
        assert snapshot['type'] == 'events.snapshot'
        assert snapshot['payload']['character']['persona_id'] in {
            'sweetiebot_default',
            'sweetiebot_convention',
            'sweetiebot_companion',
        }
        assert 'llm' in snapshot['payload']

        client.post('/character/persona', json={'persona_id': 'sweetiebot_companion'})
        persona_event = websocket.receive_json()
        assert persona_event['type'] == 'persona.selected'
        assert persona_event['payload']['character']['persona_id'] == 'sweetiebot_companion'

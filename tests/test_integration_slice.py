import asyncio

from fastapi.testclient import TestClient

from sweetiebot.api.app import EventEnvelope, create_app


def test_operator_web_surface_endpoints_exist() -> None:
    client = TestClient(create_app())

    character = client.get('/character')
    assert character.status_code == 200
    assert character.json()['persona_id'] == 'sweetiebot_default'

    accessories = client.get('/accessories')
    assert accessories.status_code == 200
    assert 'active_scene' in accessories.json()
    assert accessories.json()['audio']['sink'] in {'disabled', 'cerberus_go2_onboard_audio'}

    memory = client.get('/memory/summary')
    assert memory.status_code == 200
    assert 'known_people' in memory.json()
    assert 'preferences' in memory.json()


def test_websocket_stream_emits_snapshot_and_bridge_events() -> None:
    app = create_app()
    client = TestClient(app)

    with client.websocket_connect('/ws/events') as websocket:
        snapshot = websocket.receive_json()
        assert snapshot['type'] == 'events.snapshot'
        assert 'accessories' in snapshot['payload']
        assert 'memory' in snapshot['payload']
        assert 'plugins' in snapshot['payload']

        asyncio.run(
            app.state.event_hub.publish(
                EventEnvelope(
                    'persona.selected',
                    'sweetiebot_persona',
                    {
                        'character': {'persona_id': 'sweetiebot_companion'},
                        'active_routine': 'greeting_01',
                    },
                )
            )
        )
        event = websocket.receive_json()
        assert event['type'] == 'persona.selected'
        assert event['payload']['character']['persona_id'] == 'sweetiebot_companion'
        assert event['payload']['active_routine'] == 'greeting_01'

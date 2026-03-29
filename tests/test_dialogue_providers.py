import httpx

from sweetiebot.accessories.audio_output import CerberusAudioClient
from sweetiebot.dialogue.providers import AnthropicMessagesProvider, OpenAIResponsesProvider


def test_openai_provider_extracts_output_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith('/responses')
        return httpx.Response(200, json={'output_text': 'Hi everypony from OpenAI!'})

    provider = OpenAIResponsesProvider(
        api_key='test-key',
        model='gpt-test',
        base_url='https://api.openai.test/v1',
        transport=httpx.MockTransport(handler),
    )
    result = provider.generate_reply(system_prompt='be cute', user_text='hello')
    assert result.provider == 'openai'
    assert 'everypony' in result.text.lower()


def test_anthropic_provider_extracts_text_block() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith('/v1/messages')
        return httpx.Response(
            200,
            json={'content': [{'type': 'text', 'text': 'Hello from Claude!'}]},
        )

    provider = AnthropicMessagesProvider(
        api_key='test-key',
        model='claude-test',
        base_url='https://api.anthropic.test',
        transport=httpx.MockTransport(handler),
    )
    result = provider.generate_reply(system_prompt='be cute', user_text='hello')
    assert result.provider == 'anthropic'
    assert 'claude' in result.text.lower()


def test_cerberus_audio_client_dispatches_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith('/audio/speak')
        payload = request.read().decode()
        assert 'sweetie-default' in payload
        return httpx.Response(200, json={'queued': True})

    client = CerberusAudioClient(
        base_url='http://cerberus.test',
        speak_path='/audio/speak',
        transport=httpx.MockTransport(handler),
    )
    result = client.speak(text='Testing one two three')
    assert result.ok is True
    assert result.sink == 'cerberus_go2_onboard_audio'

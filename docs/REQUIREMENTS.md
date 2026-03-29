# Requirements

## Runtime
- Python 3.11+
- FastAPI
- Uvicorn
- httpx
- PyYAML

## Optional external services
- OpenAI API key for Responses API use
- Anthropic API key for Messages API use
- reachable CERBERUS endpoint that exposes onboard audio playback

## Design constraints
- no direct actuator control from the language model
- all speech remains short and operator-friendly
- hardware adapters must be optional and configurable
- local fallback must remain available when no API key is set

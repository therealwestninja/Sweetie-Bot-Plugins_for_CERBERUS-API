# 🤖 Sweetie-Bot Plugin Ecosystem

Sweetie-Bot is a modular plugin ecosystem built to extend and enhance the CERBERUS robotics platform.

## What is this?
A drop-in system of containerized plugins that:
- Extend CERBERUS API functionality
- Add AI, autonomy, personality, and control layers
- Allow developers to build reusable robotics modules

## Included Plugins
- cerberus-bridge
- character
- memory
- autonomy
- input
- audio
- emotion

## Quick Start

```bash
docker-compose up --build
```

## Architecture

Core Concepts:
- Plugins communicate via HTTP
- Standard `/execute` endpoint
- Shared schema (type + payload)
- Stateless design where possible

## Plugin API Contract

POST /execute

```json
{
  "type": "action.type",
  "payload": {}
}
```

## How to Make Your Own Plugin

1. Copy plugin template
2. Implement `/execute`
3. Define capabilities in plugin.yaml
4. Build Docker image

## Coming Soon

- AI control
- Improved learning
- Detection
- Pathing
- Reasoning
- Real-world adaptation

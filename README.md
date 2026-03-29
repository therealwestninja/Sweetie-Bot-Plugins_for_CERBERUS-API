# 🌸 Sweetie Bot (CERBERUS API Framework)

A modular, plugin-driven AI character runtime designed for expressive, reactive, and embodied agents.

## What is Sweetie Bot?
Sweetie Bot is a framework for building a stateful, reactive AI character with memory, mood, attention, behavior, and telemetry.

## Core Pipeline
Input → Memory → Mood → Attention → Behavior → Routine Arbitration → Output

## Features
- Character State (mood, focus, routines)
- Memory system
- Mood engine
- Attention system
- Behavior director
- Routine arbitration
- Telemetry system
- Plugin architecture
- FastAPI + CLI interfaces

## Installation
```bash
git clone https://github.com/therealwestninja/Sweetie-Bot_for_CERBERUS-API.git
cd Sweetie-Bot_for_CERBERUS-API
pip install -r requirements.txt
```

## Run API
```bash
uvicorn sweetiebot.api.app:app --reload
```

## Run CLI
```bash
python -m sweetiebot.cli.main state-show
```

## Project Structure
sweetiebot/
├── api/
├── behavior/
├── mood/
├── attention/
├── routines/
├── telemetry/
├── plugins/
├── state/
├── memory/
├── runtime.py

## Status
Early framework, core systems complete, expanding features.

## Future
- Perception system
- LLM dialogue
- Hardware integration
- Advanced behaviors


import asyncio
from sweetiebot.runtime.events import event_bus, make_event
from sweetiebot.runtime.cerberus_adapter import send_to_cerberus

async def execute_action(action: dict):
    result = await send_to_cerberus(action)
    await event_bus.emit(make_event(
        "cerberus.execution_ack",
        result,
        source="cerberus"
    ))

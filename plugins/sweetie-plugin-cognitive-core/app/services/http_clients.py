from __future__ import annotations
from typing import Any, Dict
import httpx

async def call_execute(url: str, payload: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{url.rstrip('/')}/execute", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception:
        return None

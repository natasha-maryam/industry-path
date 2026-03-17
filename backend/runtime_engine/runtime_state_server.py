from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket

from runtime_engine.runtime_telemetry import runtime_telemetry


logger = logging.getLogger(__name__)


async def runtime_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("runtime telemetry websocket connected")
    try:
        while True:
            await websocket.send_json(runtime_telemetry.get_all_tags())
            await asyncio.sleep(0.1)
    except Exception:
        logger.info("runtime telemetry websocket disconnected")
        await websocket.close()

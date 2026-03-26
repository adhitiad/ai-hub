import asyncio
import json

from fastapi import WebSocket

from src.core.logger import logger
from src.database.redis_client import redis_client


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, symbol: str):
        await websocket.accept()
        if symbol not in self.active_connections:
            self.active_connections[symbol] = []
        self.active_connections[symbol].append(websocket)
        logger.info(f"🔌 WS Connected: {symbol}")

    def disconnect(self, websocket: WebSocket, symbol: str):
        if symbol in self.active_connections:
            if websocket in self.active_connections[symbol]:
                self.active_connections[symbol].remove(websocket)
            if not self.active_connections[symbol]:
                del self.active_connections[symbol]
        logger.info(f"🔌 WS Disconnected: {symbol}")

    async def broadcast(self, symbol: str, data: dict):
        if symbol in self.active_connections:
            connections = self.active_connections[symbol]
            for ws in list(connections):
                try:
                    await ws.send_json(data)
                except Exception:
                    self.disconnect(ws, symbol)


manager = ConnectionManager()


async def redis_connector_task():
    """
    Mendengarkan Redis Pub/Sub dan mem-push ke WebSocket
    HANYA ketika ada data (event) baru dari producer.py.
    """
    await redis_client.connect()
    redis_conn = redis_client.redis
    if redis_conn:
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe("signal:all")

        logger.info("🎧 Redis Pub/Sub WS Listener Started")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    symbol = data.get("Symbol")

                    # Tambahkan server timestamp
                    data["server_time"] = str(asyncio.get_event_loop().time())

                    if symbol and symbol in manager.active_connections:
                        await manager.broadcast(symbol, data)

                except Exception as e:
                    logger.error(f"WS Broadcast Error: {e}")

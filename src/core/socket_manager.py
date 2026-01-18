# src/core/socket_manager.py
import asyncio
import json
import random

from fastapi import WebSocket, WebSocketDisconnect

from src.core.logger import logger
from src.core.redis_client import redis_client
from src.core.signal_bus import signal_bus


class ConnectionManager:
    def __init__(self):
        # Simpan koneksi aktif: {"BBCA.JK": [ws1, ws2]}
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

    async def broadcast(self, symbol: str, data: dict):
        """Broadcast data to all WebSocket clients subscribed to a symbol."""
        if symbol in self.active_connections:
            connections = self.active_connections[symbol]
            for ws in list(connections):  # Copy list for safety
                try:
                    await ws.send_json(data)
                except Exception:
                    self.disconnect(ws, symbol)


manager = ConnectionManager()


async def redis_connector_task():
    """
    Task ini mendengarkan Redis Pub/Sub dan mem-push ke WebSocket
    HANYA ketika ada data baru. Tanpa polling.
    """
    await redis_client.connect()
    redis_conn = redis_client.redis
    if redis_conn:
        pubsub = redis_conn.pubsub()

        # Subscribe ke channel global (atau logic specific channel)
        await pubsub.subscribe("signal:all")

        logger.info("🎧 Redis Pub/Sub Listener Started")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    symbol = data.get("Symbol")

                    # Push hanya ke client yang subscribe simbol ini
                    if symbol and symbol in manager.active_connections:
                        connections = manager.active_connections[symbol]
                        for ws in list(connections):  # Copy list agar aman
                            try:
                                await ws.send_json(data)
                            except Exception:
                                manager.disconnect(ws, symbol)

                except Exception as e:
                    logger.error(f"WS Broadcast Error: {e}")


# --- Background Task Real-Time Stream ---
async def broadcast_market_data():
    """
    Mengirim data terbaru dari Signal Bus ke Frontend via WebSocket.
    """
    while True:
        if manager.active_connections:
            active_symbols = list(manager.active_connections.keys())

            for symbol in active_symbols:
                # 1. AMBIL DATA REAL DARI SIGNAL BUS (Hasil AI)
                ai_data = await signal_bus.get_signal(symbol)

                if ai_data:
                    # Kirim paket lengkap (Price, Action, Tp, Sl, Prob, Analysis)
                    payload = ai_data
                    # Tambahkan timestamp server agar frontend tau ini data baru
                    payload["server_time"] = str(asyncio.get_event_loop().time())

                    await manager.broadcast(symbol, payload)
                else:
                    # Jika AI belum selesai loading, kirim status 'Loading...'
                    # atau fallback ke dummy price sementara agar chart jalan
                    fallback_data = {
                        "Symbol": symbol,
                        "Price": round(random.uniform(100, 200), 2),  # Placeholder
                        "Action": "LOADING...",
                        "Prob": "0%",
                        "AI_Analysis": "Initializing AI models...",
                    }
                    await manager.broadcast(symbol, fallback_data)

        # Update setiap 1 detik (Sesuaikan jika ingin lebih cepat/lambat)
        await asyncio.sleep(1)

        # Update setiap 1 detik (Sesuaikan jika ingin lebih cepat/lambat)
        await asyncio.sleep(1)

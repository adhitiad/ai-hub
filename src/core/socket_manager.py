import asyncio
import json
import random  # Simulasi harga (Nanti ganti dengan real data stream)
from typing import Dict, List

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Menyimpan koneksi aktif per symbol: {"BTCUSD": [ws1, ws2]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, symbol: str):
        await websocket.accept()
        if symbol not in self.active_connections:
            self.active_connections[symbol] = []
        self.active_connections[symbol].append(websocket)

    def disconnect(self, websocket: WebSocket, symbol: str):
        if symbol in self.active_connections:
            self.active_connections[symbol].remove(websocket)
            if not self.active_connections[symbol]:
                del self.active_connections[symbol]

    async def broadcast(self, symbol: str, data: dict):
        if symbol in self.active_connections:
            for connection in self.active_connections[symbol]:
                try:
                    await connection.send_json(data)
                except:
                    # Hapus koneksi mati
                    self.disconnect(connection, symbol)


manager = ConnectionManager()


# --- Background Task Simulasi Data Candle ---
# (Di Production, ini diganti dengan Stream dari Binance/YFinance)
async def broadcast_market_data():
    while True:
        # Simulasi kirim data untuk semua symbol yang sedang dipantau
        if manager.active_connections:
            for symbol in list(manager.active_connections.keys()):
                # Dummy Data Candle
                price_update = {
                    "symbol": symbol,
                    "price": round(random.uniform(100, 20000), 2),
                    "timestamp": asyncio.get_event_loop().time(),
                }
                await manager.broadcast(symbol, price_update)

        await asyncio.sleep(1)  # Update tiap 1 detik

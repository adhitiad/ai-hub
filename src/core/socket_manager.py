import asyncio
import json
import random
from typing import Dict, List

from fastapi import WebSocket

# IMPORT PENTING: Ambil data dari Bus Penyimpanan Sinyal
from src.core.signal_bus import signal_bus


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
            if websocket in self.active_connections[symbol]:
                self.active_connections[symbol].remove(websocket)
            if not self.active_connections[symbol]:
                del self.active_connections[symbol]

    async def broadcast(self, symbol: str, data: dict):
        if symbol in self.active_connections:
            # Copy list untuk menghindari error 'changed size during iteration'
            for connection in list(self.active_connections[symbol]):
                try:
                    await connection.send_json(data)
                except Exception:
                    # Hapus koneksi mati secara aman
                    self.disconnect(connection, symbol)


manager = ConnectionManager()


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
                ai_data = signal_bus.get_signal(symbol)

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

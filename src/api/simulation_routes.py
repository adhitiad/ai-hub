import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocket

from src.core.database import db
from src.core.logger import logger

router = APIRouter(prefix="/simulation", tags=["Time Travel"])


@router.websocket("/replay/{symbol}")
async def replay_market_data(websocket: WebSocket, symbol: str, date: str):
    """
    WebSocket endpoint.
    Client connect -> Server kirim data per menit dari tanggal tertentu.
    Format date: YYYY-MM-DD
    """
    await websocket.accept()

    try:
        # 1. Ambil data historis dari DB
        start_dt = datetime.strptime(date, "%Y-%m-%d")

        cursor = (
            db.market_data.find({"symbol": symbol, "timestamp": {"$gte": start_dt}})
            .sort("timestamp", 1)
            .limit(1000)
        )  # Batasi 1000 candle

        history_data = await cursor.to_list(length=1000)

        if not history_data:
            await websocket.send_text("No data found for this date.")
            await websocket.close()
            return

        # 2. Loop dan Kirim (Simulasi Real-time)
        for candle in history_data:
            payload = {
                "time": candle["timestamp"].isoformat(),
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "volume": candle["volume"],
            }

            await websocket.send_json(payload)

            # 3. Artificial Delay (Speed 1 detik = 1 candle 5 menit)
            # Biar user kerasa "nonton" chart jalan
            await asyncio.sleep(0.5)

        await websocket.send_text("Replay Finished")
        await websocket.close()

    except Exception as e:
        logger.error(f"Replay Error: {e}")
        await websocket.close()

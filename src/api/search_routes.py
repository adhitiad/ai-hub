import asyncio

from fastapi import APIRouter, Depends, Query

from src.api.auth import get_current_user
from src.core.config_assets import ASSETS
from src.database.database import assets_collection
from src.database.signal_bus import signal_bus

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/")
async def search_assets(
    q: str = Query(..., min_length=2), user: dict = Depends(get_current_user)
):
    """
    Mencari aset berdasarkan simbol atau nama.
    Membaca dari database terlebih dahulu, fallback ke config statis.
    Contoh: q=BBCA -> Returns BBCA.JK info + Active Signal status
    """
    query = q.upper()
    results = []

    # 1. Coba dari database MongoDB
    try:
        cursor = assets_collection.find(
            {"symbol": {"$regex": query, "$options": "i"}}, {"_id": 0}
        ).limit(10)
        db_assets = await cursor.to_list(length=10)
    except Exception:
        db_assets = []

    if db_assets:
        for asset in db_assets:
            symbol = asset.get("symbol", "")
            active_signal = await signal_bus.get_signal(symbol)
            if asyncio.iscoroutine(active_signal):
                active_signal = await active_signal

            status = "Idle"
            if active_signal and isinstance(active_signal, dict):
                status = active_signal.get("Action", "HOLD")

            results.append(
                {
                    "symbol": symbol,
                    "category": asset.get("category", "UNKNOWN"),
                    "type": asset.get("type", "unknown"),
                    "status": status,
                    "has_signal": bool(active_signal),
                }
            )
    else:
        # 2. Fallback ke ASSETS config
        for category, items in ASSETS.items():
            for symbol, info in items.items():
                if query in symbol:
                    active_signal = await signal_bus.get_signal(symbol)
                    if asyncio.iscoroutine(active_signal):
                        active_signal = await active_signal

                    status = "Idle"
                    if active_signal and isinstance(active_signal, dict):
                        status = active_signal.get("Action", "HOLD")

                    results.append(
                        {
                            "symbol": symbol,
                            "category": category,
                            "type": info["type"],
                            "status": status,
                            "has_signal": bool(active_signal),
                        }
                    )

    return results[:10]

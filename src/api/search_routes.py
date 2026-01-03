from fastapi import APIRouter, Depends, Query

from src.api.auth import get_current_user
from src.core.config_assets import ASSETS
from src.core.signal_bus import signal_bus

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/")
def search_assets(
    q: str = Query(..., min_length=2), user: dict = Depends(get_current_user)
):
    """
    Mencari aset berdasarkan simbol atau nama.
    Contoh: q=BBCA -> Returns BBCA.JK info + Active Signal status
    """
    query = q.upper()
    results = []

    # 1. Loop semua konfigurasi aset
    for category, items in ASSETS.items():
        for symbol, info in items.items():
            # Cek pencocokan string
            if query in symbol:
                # Cek apakah ada sinyal aktif di RAM (Signal Bus)
                active_signal = signal_bus.get_signal(symbol)

                status = "Idle"
                if active_signal:
                    status = active_signal.get("Action", "HOLD")

                results.append(
                    {
                        "symbol": symbol,
                        "category": category,
                        "type": info["type"],
                        "status": status,  # BUY, SELL, HOLD, atau Idle
                        "has_signal": bool(active_signal),
                    }
                )

    # Limit hasil biar gak kebanyakan
    return results[:10]

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from src.api.auth import get_current_user
from src.database.signal_bus import signal_bus

router = APIRouter(prefix="/screener", tags=["Stock Screener"])


@router.get("/run")
async def run_screener(
    min_score: int = 0,
    rsi_max: float = 100,
    rsi_min: float = 0,
    signal_only: bool = False,
    bandar_accum: bool = False,
    user: dict = Depends(get_current_user),
):
    """
    Menyaring aset berdasarkan indikator yang sudah dihitung di backend (Memory).
    """
    all_signals = await signal_bus.get_all_signals()  # Data real-time dari RAM
    results = []

    for symbol, data in all_signals.items():
        # Parsing data dari signal bus (pastikan formatnya konsisten dengan producer)
        # Asumsi data di bus memiliki field 'Technical' yang lengkap

        # Mockup logic karena data di bus saat ini berbentuk 'Signal Response'
        # Di implementation producer.py, Anda harus menyimpan RAW indicators juga ke bus.

        # Contoh filter dummy berdasarkan respons API yang ada:
        action = data.get("Action", "HOLD")

        # Filter 1: Signal
        if signal_only and action == "HOLD":
            continue

        # Filter 2: Bandar Flow (Parse dari string output jika perlu, atau ubah producer agar simpan raw data)
        if bandar_accum:
            bandar_info = data.get("Bandar_Info", {})
            if "ACCUMULATION" not in bandar_info.get("Status", ""):
                continue

        # Jika lolos filter
        results.append(data)

    return {"count": len(results), "matches": results}

import pandas as pd

from src.core.database import signals_collection


async def get_mistake_history(symbol):
    """
    Mengambil data trading yang berakhir LOSS untuk simbol tertentu.
    Ini akan menjadi 'Ingatan Buruk' yang harus dihindari AI.
    """
    # Cari sinyal yang statusnya LOSS
    cursor = signals_collection.find({"symbol": symbol, "status": "LOSS"})

    mistakes = await cursor.to_list(length=5000)

    if not mistakes:
        return {}

    # Kita butuh mapping: Kapan kejadiannya -> Apa aksinya
    # Format: { "2024-01-20 10:00": 1 }  (1 = BUY)
    mistake_map = {}

    for m in mistakes:
        # Kita perlu waktu entry (saat keputusan dibuat)
        # Pastikan di database fieldnya 'created_at' atau 'entry_time'
        # Kita ambil jam-nya saja agar cocok dengan data candle 1H
        entry_time = m.get("created_at")
        action = 1 if m["action"] == "BUY" else 2

        if entry_time:
            # Rounding ke jam terdekat (Simplifikasi pencocokan data)
            # YFinance index biasanya timestamp. Kita konversi ke string atau timestamp yang sama.
            # Disini kita simpan sebagai string sederhana dulu
            key_time = entry_time.strftime("%Y-%m-%d %H:00:00")
            mistake_map[key_time] = action

    return mistake_map

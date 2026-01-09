from datetime import datetime, time

import pytz

# Zona Waktu Jakarta (WIB)
JAKARTA_TZ = pytz.timezone("Asia/Jakarta")


def is_market_open(asset_category: str) -> bool:
    """
    Cek apakah pasar buka berdasarkan kategori aset.
    Mengembalikan True jika market sedang aktif (Sesi 1 atau Sesi 2).
    """
    now = datetime.now(JAKARTA_TZ)
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()  # 0=Senin, 4=Jumat, 5=Sabtu, 6=Minggu

    # --- 1. LOGIKA FOREX (24/5) ---
    if asset_category == "FOREX":
        # Forex tutup di weekend (Sabtu pagi - Senin pagi waktu Indo)
        if weekday >= 5:
            return False
        # High spread hours during rollover
        if 4 <= hour <= 6:
            return False
        return True

    # --- 2. LOGIKA SAHAM INDO (IDX) ---
    if asset_category == "STOCKS_INDO":
        # Libur Akhir Pekan
        if weekday >= 5:
            return False

        current_time = now.time()

        # JADWAL JUMAT (Khusus)
        if weekday == 4:
            # Sesi 1: 09:00 - 11:30
            session_1 = time(9, 0) <= current_time <= time(11, 30)
            # Sesi 2: 14:00 - 15:50 (Kita stop sebelum Pre-closing biar aman)
            session_2 = time(14, 0) <= current_time <= time(15, 50)

        # JADWAL SENIN - KAMIS
        else:
            # Sesi 1: 09:00 - 12:00
            session_1 = time(9, 0) <= current_time <= time(12, 0)
            # Sesi 2: 13:30 - 15:50
            session_2 = time(13, 30) <= current_time <= time(15, 50)

        # Pre-Opening (08:45 - 08:59) - Opsional, kita anggap buka untuk siap-siap
        pre_opening = time(8, 45) <= current_time <= time(8, 59)

        return session_1 or session_2 or pre_opening

    # Default Open untuk aset lain (US Stocks, Crypto, dll)
    return True
    # Default Open untuk aset lain (US Stocks, Crypto, dll)

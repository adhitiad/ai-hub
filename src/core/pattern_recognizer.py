import pandas as pd
import pandas_ta as ta


def detect_chart_patterns(df):
    """
    Mendeteksi pola candlestick (AI Vision) menggunakan Pandas-TA.
    Mengenali: Engulfing, Harami, Doji, Stars, Three Soldiers, dll.
    Output:
        - score (int): Total skor sentimen (-100 s/d 100)
        - patterns (list): Daftar nama pola yang terdeteksi
    """
    # Copy dataframe agar tidak mengganggu data asli
    work_df = df.copy()

    # 1. Jalankan Deteksi Semua Pola ('all')
    # Ini akan menambahkan banyak kolom baru berawalan 'CDL_'
    # Warning: Ini agak berat, pastikan server kuat. Jika lambat, pilih pola spesifik saja.
    work_df.ta.cdl_pattern(name="all", append=True)

    # Ambil baris terakhir (candle terbaru)
    last_row = work_df.iloc[-1]

    # Filter kolom yang berawalan 'CDL_'
    pattern_cols = [c for c in work_df.columns if c.startswith("CDL_")]

    detected_patterns = []
    total_score = 0

    # Bobot Pola (Bisa disesuaikan)
    # Beberapa pola lebih kuat sinyalnya daripada yang lain
    WEIGHTS = {
        "CDL_ENGULFING": 2.0,  # Reversal Kuat
        "CDL_MORNINGSTAR": 2.0,  # Reversal Kuat
        "CDL_EVENINGSTAR": 2.0,
        "CDL_HAMMER": 1.5,
        "CDL_SHOOTINGSTAR": 1.5,
        "CDL_DOJI": 0.5,  # Indecision (Lemah)
        "CDL_SPINNINGTOP": 0.5,
    }

    for col in pattern_cols:
        val = last_row[col]
        if val != 0:
            # Pandas-TA return 100 (Bullish) atau -100 (Bearish)

            # Bersihkan nama kolom (misal: CDL_ENGULFING -> Engulfing)
            pattern_name = col.replace("CDL_", "").replace("_", " ").title()

            # Tentukan Arah
            sentiment = "Bullish" if val > 0 else "Bearish"
            detected_patterns.append(f"{sentiment} {pattern_name}")

            # Hitung Skor
            # Normalisasi 100 -> 1, -100 -> -1
            base_score = 10 if val > 0 else -10

            # Kalikan dengan bobot kekuatan pola
            multiplier = WEIGHTS.get(col, 1.0)
            total_score += base_score * multiplier

    # Clamping Score agar tidak lebih dari -100 s/d 100
    total_score = max(min(total_score, 100), -100)

    return int(total_score), detected_patterns

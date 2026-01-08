import numpy as np
import pandas as pd


def detect_chart_patterns(df):
    """
    Mendeteksi pola candlestick secara manual (Native Python) tanpa dependency TA-Lib.
    Mengenali: Engulfing, Hammer, Shooting Star, Doji, Marubozu.

    Output:
        - score (int): Total skor sentimen (-100 s/d 100)
        - patterns (list): Daftar nama pola yang terdeteksi
    """
    if df.empty or len(df) < 3:
        return 0, []

    # Ambil 2 candle terakhir untuk perbandingan
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    patterns = []
    score = 0

    # --- Helper Values ---
    # Current Candle
    c_open, c_high, c_low, c_close = (
        curr["Open"],
        curr["High"],
        curr["Low"],
        curr["Close"],
    )
    c_body = abs(c_close - c_open)
    c_range = c_high - c_low
    c_upper_wick = c_high - max(c_close, c_open)
    c_lower_wick = min(c_close, c_open) - c_low

    # Previous Candle
    p_open, p_high, p_low, p_close = (
        prev["Open"],
        prev["High"],
        prev["Low"],
        prev["Close"],
    )
    p_body = abs(p_close - p_open)

    # Hindari pembagian dengan nol
    if c_range == 0:
        c_range = 0.00001

    # ==========================
    # 1. DOJI (Indecision)
    # ==========================
    # Body sangat tipis (< 10% dari total range)
    if (c_body / c_range) < 0.1:
        # Cek tipe Doji
        if c_lower_wick > 3 * c_body and c_upper_wick < c_body:
            patterns.append("Bullish Dragonfly Doji")
            score += 10
        elif c_upper_wick > 3 * c_body and c_lower_wick < c_body:
            patterns.append("Bearish Gravestone Doji")
            score -= 10
        else:
            patterns.append("Neutral Doji")
            # Score 0 atau +5/-5 tergantung tren (disini netral dulu)

    # ==========================
    # 2. HAMMER & HANGING MAN
    # ==========================
    # Lower wick panjang (> 2x body), Upper wick kecil
    elif c_lower_wick > 2 * c_body and c_upper_wick < c_body:
        # Hammer (Bullish) biasanya di lembah, Hanging Man (Bearish) di puncak
        # Kita asumsikan Bullish signal sederhana
        patterns.append("Bullish Hammer")
        score += 15

    # ==========================
    # 3. SHOOTING STAR & INVERTED HAMMER
    # ==========================
    # Upper wick panjang (> 2x body), Lower wick kecil
    elif c_upper_wick > 2 * c_body and c_lower_wick < c_body:
        # Shooting Star (Bearish)
        patterns.append("Bearish Shooting Star")
        score -= 15

    # ==========================
    # 4. ENGULFING (Kuat)
    # ==========================
    # Bullish Engulfing: Prev Merah, Curr Hijau. Body Curr "menelan" Prev.
    if (p_close < p_open) and (c_close > c_open):
        if c_close > p_open and c_open < p_close:
            patterns.append("Bullish Engulfing")
            score += 25

    # Bearish Engulfing: Prev Hijau, Curr Merah.
    elif (p_close > p_open) and (c_close < c_open):
        if c_close < p_open and c_open > p_close:
            patterns.append("Bearish Engulfing")
            score -= 25

    # ==========================
    # 5. MARUBOZU (Momentum)
    # ==========================
    # Body penuh (> 90% range), wick sangat kecil
    if (c_body / c_range) > 0.9:
        if c_close > c_open:
            patterns.append("Bullish Marubozu")
            score += 10
        else:
            patterns.append("Bearish Marubozu")
            score -= 10

    # Clamping Score agar tetap di range -100 s/d 100
    total_score = max(min(score, 100), -100)

    return int(total_score), patterns

import numpy as np
import pandas as pd

from src.core.smart_money import analyze_smart_money


def calculate_technical_score(df):
    """
    Menghitung Technical Score Global (0-100)
    Menggabungkan: Trend, Momentum (RSI), MACD, dan Smart Money Concept (SMC).

    Returns:
        score (int): Nilai -100 s/d 100
        signal (str): STRONG BUY, BUY, NEUTRAL, SELL, STRONG SELL
        analysis (str): Ringkasan analisis text
    """
    if df.empty or len(df) < 50:
        return 0, "NEUTRAL", "Not enough data"

    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0
    reasons = []

    # --- 1. TREND ANALYSIS (Max 40 Poin) ---
    # SMA 50 vs SMA 200 (Major Trend)
    if "SMA_50" in df.columns and "SMA_200" in df.columns:
        if last["SMA_50"] > last["SMA_200"]:
            score += 20
            reasons.append("Uptrend Major")
        else:
            score -= 20
            reasons.append("Downtrend Major")

    # Price vs SMA 20 (Short Term Trend)
    if "SMA_20" in df.columns:
        if last["Close"] > last["SMA_20"]:
            score += 10
        else:
            score -= 10

    # --- 2. MOMENTUM RSI (Max 30 Poin) ---
    rsi = last.get("RSI_14", 50)

    if rsi < 30:
        score += 30
        reasons.append("Oversold (Reversal)")
    elif rsi > 70:
        score -= 30
        reasons.append("Overbought (Reversal)")
    elif 50 <= rsi <= 70:
        score += 10  # Bullish Momentum
    elif 30 <= rsi < 50:
        score -= 10  # Bearish Momentum

    # --- 3. MACD (Max 20 Poin) ---
    macd = last.get("MACD_12_26_9", 0)
    macd_signal = last.get("MACDs_12_26_9", 0)

    if macd > macd_signal:
        score += 15
        # Crossover baru terjadi?
        prev_macd = prev.get("MACD_12_26_9", 0)
        prev_signal = prev.get("MACDs_12_26_9", 0)
        if prev_macd <= prev_signal:
            score += 5
            reasons.append("MACD Golden Cross")
    else:
        score -= 15

    # --- 4. SMART MONEY CONCEPT (SMC) (Max 30 Poin) ---
    sm_analysis = analyze_smart_money(df)

    if sm_analysis["detected"]:
        # Tambahkan skor dari Smart Money (bisa positif atau negatif)
        sm_score = sm_analysis.get("score", 0)
        score += sm_score
        reasons.append(sm_analysis["message"])

    # --- FINALIZATION ---
    # Normalisasi Score agar tetap di range -100 s/d 100
    score = max(min(score, 100), -100)

    # Tentukan Signal Text
    if score >= 75:
        signal = "STRONG BUY"
    elif score >= 25:
        signal = "BUY"
    elif score <= -75:
        signal = "STRONG SELL"
    elif score <= -25:
        signal = "SELL"
    else:
        signal = "NEUTRAL"

    # Buat Summary Analysis
    analysis_str = ", ".join(reasons)
    if not analysis_str:
        analysis_str = "Sideways / No clear pattern"

    return score, signal, analysis_str


def calculate_stock_score(df, bandar_data=None):
    """
    Legacy function untuk Saham Indo (Kompatibilitas lama)
    """
    # Gunakan logic baru tapi mapping ke format lama
    tech_score, _, _ = calculate_technical_score(df)

    # Ubah range -100..100 menjadi 0..100
    normalized_tech = (tech_score + 100) / 2

    bandar_score = 50
    if bandar_data:
        bandar_score = bandar_data.get("score", 50)

    final_score = (normalized_tech * 0.6) + (bandar_score * 0.4)

    grade = "E"
    if final_score >= 80:
        grade = "A"
    elif final_score >= 60:
        grade = "B"
    elif final_score >= 40:
        grade = "C"

    return {
        "total_score": round(final_score, 1),
        "grade": grade,
        "details": {"technical": normalized_tech, "bandar": bandar_score},
    }

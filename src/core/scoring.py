import numpy as np
import pandas as pd


def calculate_stock_score(df, bandar_data=None):
    """
    Menghitung Skor Saham (0-100) berdasarkan Technical & Bandarmology.
    """
    score = 0
    weights = {"tech": 0.6, "bandar": 0.4}  # Bobot penilaian

    last = df.iloc[-1]

    # 1. Technical Score (Max 100)
    tech_score = 50  # Base

    # RSI (Momentum)
    if 40 < last["RSI_14"] < 70:
        tech_score += 10
    elif last["RSI_14"] <= 30:
        tech_score += 20  # Oversold bounce potential

    # Trend (MA)
    if last["Close"] > last["SMA_50"]:
        tech_score += 15
    if last["SMA_20"] > last["SMA_50"]:
        tech_score += 15  # Golden Cross area

    # MACD
    if last["MACD_12_26_9"] > last["MACDs_12_26_9"]:
        tech_score += 10

    # 2. Bandar Score (Max 100)
    bandar_score = 50
    if bandar_data:
        bandar_score = bandar_data.get("score", 50)

    # 3. Final Calculation
    final_score = (tech_score * weights["tech"]) + (bandar_score * weights["bandar"])

    # Grading
    grade = "E"
    if final_score >= 90:
        grade = "A+"
    elif final_score >= 80:
        grade = "A"
    elif final_score >= 70:
        grade = "B"
    elif final_score >= 60:
        grade = "C"
    elif final_score >= 40:
        grade = "D"

    return {
        "total_score": round(final_score, 1),
        "grade": grade,
        "details": {"technical": tech_score, "bandar": bandar_score},
    }

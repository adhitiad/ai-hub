import glob  # <--- Tambahkan ini
import os

import numpy as np
import torch
from stable_baselines3 import PPO

from src.core.agent_torch import ForexTraderNet, optimize_model_for_inference
from src.core.bandarmology import analyze_bandar_flow
from src.core.config_assets import get_asset_info
from src.core.data_loader import fetch_data
from src.core.llm_analyst import consult_groq_analyst
from src.core.market_structure import check_mtf_trend, detect_insider_volume  # <--- NEW
from src.core.money_management import calculate_lot_size
from src.core.news_collector import analyze_news_sentiment, fetch_market_news
from src.core.pattern_recognizer import detect_chart_patterns  # <--- NEW
from src.core.smart_money import analyze_forex_whale
from src.core.torch_config import device
from src.core.vector_db import recall_similar_events  # <--- Import

MODEL_DIR = "models"
MODEL_PATH = "models/forex_net.pt"

cached_model = None


def load_optimized_model(input_dim=14):
    global cached_model
    if cached_model:
        return cached_model

    if not os.path.exists(MODEL_PATH):
        return None

    model = ForexTraderNet(input_size=input_dim)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    optimized_model = optimize_model_for_inference(model)

    cached_model = optimized_model
    return cached_model


# --- PERUBAHAN UTAMA DISINI ---
# Kita hapus 'get_asset_info' dan ganti parameternya menerima 'asset_info' langsung
def get_detailed_signal(symbol, asset_info, custom_balance=None):
    """
    Analisis sinyal menggunakan data aset yang dikirim dari Database.
    """
    info = get_asset_info(symbol)

    if not info:
        return {"error": "Asset not config."}
    if not asset_info:
        return {"error": "Asset info missing."}

    asset_type = info["type"]

    safe_symbol = symbol.replace("=", "").replace("^", "")
    category = info["category"].lower()
    base_dir = f"{MODEL_DIR}/{category}"

    # 1. Cari semua file model: SYMBOL_*.zip (bisa yang ada tanggal atau tidak)
    # Contoh: BBCA.JK_2024-10-27.zip
    pattern = f"{base_dir}/{safe_symbol}*.zip"
    files = glob.glob(pattern)

    if not files:
        return {"Symbol": symbol, "Action": "HOLD", "Reason": "No Model Trained"}

    # 2. Sortir file (Nama file dengan tanggal YYYY-MM-DD bisa disort text)
    # File dengan tanggal terbesar (terbaru) akan di index 0
    files.sort(reverse=True)
    model_path = files[0]
    try:
        model = PPO.load(model_path)
        df = fetch_data(symbol, period="1mo", interval="1h")
        if df.empty:
            return {"Symbol": symbol, "Action": "HOLD", "Reason": "No Data"}

        last_row = df.iloc[-1]
        obs = np.append(last_row.values, [0])
        action, _ = model.predict(obs)

        confidence = 85.5
        action_map = {0: "HOLD", 1: "BUY", 2: "SELL"}
        act_str = action_map[int(action)]

        if act_str == "HOLD":
            return {"Symbol": symbol, "Action": "HOLD"}

        current_price = last_row["Close"]
        atr = last_row["ATR_14"]

        # TP SL Calculation
        sl_dist = atr * 1.5
        tp, sl = 0, 0

        news = fetch_market_news(symbol)
        sent_score, sent_reason = analyze_news_sentiment(symbol, news)
        historical_events = recall_similar_events(sent_reason, n_results=2)

        history_note = ""
        if historical_events:
            # Cek apakah kejadian serupa di masa lalu itu sentimennya negatif/positif
            similar_sentiment_avg = sum(
                h["past_sentiment"] for h in historical_events
            ) / len(historical_events)

            # Buat narasi tambahan
            history_note = f"\n📚 Historical Context: Similar news in the past had avg sentiment {similar_sentiment_avg:.1f}."

            # Logika Penguat Sinyal
            # Jika berita sekarang NEGATIF, dan sejarah bilang dulu juga NEGATIF -> Sinyal SELL makin kuat
            if sent_score < 0 and similar_sentiment_avg < -0.5:
                confidence = min(99, confidence + 5)
                history_note += " (Pattern Confirmed)"

        pattern_score, patterns_list = detect_chart_patterns(df)
        pattern_str = ", ".join(patterns_list) if patterns_list else "No Pattern"

        reason_str = ""  # Initialize reason_str

        # Logic: Jika pola reversal kuat terdeteksi berlawanan arah, kurangi confidence
        if act_str == "BUY" and pattern_score < -20:  # Ada pola Bearish kuat
            confidence -= 20
            reason_str += f" | ⚠️ Chart Warn: {pattern_str}"
        elif act_str == "SELL" and pattern_score > 20:  # Ada pola Bullish kuat
            confidence -= 20
            reason_str += f" | ⚠️ Chart Warn: {pattern_str}"
        elif abs(pattern_score) > 20:  # Searah
            confidence = min(99, confidence + 10)
            reason_str += f" | 👁️ Chart Confirm: {pattern_str}"

        # --- 2. MTF CONFIRMATION ---
        mtf_status, mtf_reason = check_mtf_trend(
            symbol, current_tf="1h"
        )  # Asumsi bot main H1

        # Logic: Jangan lawan Trend Besar (Follow the Giant)
        # Jika AI H1 suruh BUY, tapi H4/Daily DOWNTREND -> Bahaya
        if act_str == "BUY" and "DOWNTREND" in mtf_status:
            # Kecuali pattern reversalnya sangat kuat (>50), kita anggap ini koreksi -> Risky Buy
            if pattern_score < 50:
                act_str = "HOLD"  # Batalkan
                reason_str = f"⛔ MTF REJECT: {mtf_reason}"
                confidence = 0

        elif act_str == "SELL" and "UPTREND" in mtf_status:
            if pattern_score > -50:
                act_str = "HOLD"
                reason_str = f"⛔ MTF REJECT: {mtf_reason}"
                confidence = 0

        # --- 3. INSIDER ANOMALY ---

        # Money Management (Ambil pip_scale dari DB)
        # --- UPDATE LOGIC SALDO ---
        # Default Balance jika user tidak input
        pip_scale = asset_info.get("pip_scale", 1)
        sl_pips = sl_dist * pip_scale
        user_balance = 0

        # 2. Ambil Saldo Sesuai Input User
        if custom_balance:
            if asset_type == "stock_indo":
                user_balance = custom_balance.get(
                    "stock", 100000000
                )  # Default 100jt IDR
            else:
                user_balance = custom_balance.get("forex", 1000)  # Default 1000 USD
        else:
            # Fallback ke default sistem lama jika tidak ada input
            user_balance = 100000000 if asset_type == "stock_indo" else 1000

        # 3. Hitung Lot Size (Dynamic)
        # Sl (Stop Loss) dan current_price sudah dihitung di kode asli sebelumnya
        lot_size = calculate_lot_size(
            balance=user_balance,
            risk_percentage=2.0,  # Bisa dibuat dinamis juga nanti
            sl_price=sl,
            entry_price=current_price,
            asset_info=info,
        )

        # Format output Lot agar user paham
        lot_display = f"{lot_size} Lot"
        if asset_type == "stock_indo":
            # Tambahkan info lembar biar jelas (IDR)
            lot_display += f" ({int(lot_size * 100)} Lbr)"

        # --- LOGIKA DETEKTOR KHUSUS ---
        bandar_data = None
        smc_data = None  # Inisialisasi variabel
        whale_info = ""

        # --- 3. INSIDER ANOMALY ---
        is_insider, insider_msg = detect_insider_volume(df)
        if is_insider:
            # Jika ada aktivitas insider, ini sinyal 'High Alert'.
            # Biasanya mendahului pergerakan besar.
            # Kita bisa jadikan ini sebagai 'Signal Booster' atau 'Warning'
            reason_str += f" | {insider_msg}"

            # Tambahkan flag khusus di response
            whale_info += " [INSIDER ACTIVITY]"

        if asset_type == "stock_indo":
            bandar_data = analyze_bandar_flow(df)
            if bandar_data["score"] > 70:
                whale_info = f"Bandar Accumulation (Score: {bandar_data['score']})"
            elif bandar_data["score"] < 30:
                whale_info = f"Bandar Distribution (Score: {bandar_data['score']})"

        elif asset_type == "forex":
            smc_data = analyze_forex_whale(df)
            if smc_data and smc_data["detected"]:
                whale_info = f"{smc_data['message']} - {smc_data['strength']}"

                # Logic Intervensi Paus
                if act_str == "SELL" and smc_data["type"] == "WHALE_BUY":
                    act_str = "BUY"
                    confidence = 88.0
                elif act_str == "BUY" and smc_data["type"] == "WHALE_SELL":
                    act_str = "SELL"
                    confidence = 88.0

        # --- LOGIKA GROQ ANALYST ---
        detected_anomaly = None
        if asset_type == "stock_indo" and bandar_data and bandar_data["score"] > 75:
            detected_anomaly = bandar_data
        elif asset_type == "forex" and smc_data and smc_data["detected"]:
            detected_anomaly = smc_data

        ai_analysis = None
        reason_str = f"{sent_reason} {history_note}"

        if detected_anomaly:
            temp_signal_data = {
                "Price": current_price,
                "Action": act_str,
                "Tp": tp,
                "Sl": sl,
                "LotSize": lot_display,
            }
            ai_analysis = consult_groq_analyst(
                symbol, asset_info, temp_signal_data, detected_anomaly
            )

            if ai_analysis["decision"] == "WAIT":
                act_str = "HOLD"
                confidence = 0
                reason_str = f"🛑 AI VETO: {ai_analysis['reason']}"

            else:
                reason_str = f"✅ AI CONFIRMED: {ai_analysis['reason']}"
                confidence = 95.0

        response = {
            "Symbol": symbol,
            "Action": act_str,
            "Price": (
                round(current_price, 0)
                if asset_type == "stock_indo"
                else round(current_price, 5)
            ),
            "Tp": round(tp, 0) if asset_type == "stock_indo" else round(tp, 5),
            "Sl": round(sl, 0) if asset_type == "stock_indo" else round(sl, 5),
            "LotSize": lot_display,
            "Prob": f"{confidence}%",
            "Whale_Activity": (
                whale_info if whale_info else "No significant whale activity"
            ),
            "AI_Analysis": reason_str,
        }

        if bandar_data:
            response["Bandar_Info"] = {
                "Status": bandar_data["status"],
                "Score": f"{bandar_data['score']}/100",
                "Volume_Spike": f"{bandar_data['vol_ratio']}x Avg",
                "Analysis": bandar_data["message"],
            }

        if ai_analysis:
            response["AI_Analyst"] = {
                "Verdict": ai_analysis["decision"],
                "Projected_Profit": ai_analysis["est_profit"],
                "Projected_Loss": ai_analysis["est_loss"],
                "Risk_Level": f"{ai_analysis['risk_score']}/10",
                "Note": ai_analysis["reason"],
            }

        # Pastikan return menyertakan info saldo yang dipakai (opsional, untuk debug)
        response["Used_Balance"] = user_balance
        response["Patterns"] = pattern_str
        response["MTF_Trend"] = mtf_status
        return response

    except Exception as e:
        return {"error": str(e)}

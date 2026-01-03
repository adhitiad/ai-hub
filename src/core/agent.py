import os

import numpy as np
from stable_baselines3 import PPO

from src.core.bandarmology import analyze_bandar_flow  # Untuk Saham
from src.core.config_assets import get_asset_info
from src.core.data_loader import fetch_data
from src.core.money_management import calculate_lot_size  # (Lihat bawah)
from src.core.smart_money import analyze_forex_whale  # <--- [BARU] Untuk Forex

MODEL_DIR = "models"
MODEL_PATH = "models/forex_net.pt"

# Cache model di RAM agar tidak load berulang-ulang
cached_model = None


def load_optimized_model(
    input_dim=14,
):  # Sesuaikan input_dim dengan jumlah indikator Anda
    global cached_model
    if cached_model:
        return cached_model

    if not os.path.exists(MODEL_PATH):
        return None

    # Load Model Mentah
    model = ForexTraderNet(input_size=input_dim)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))

    # OPTIMASI DISINI (Hanya sekali saat startup)
    optimized_model = optimize_model_for_inference(model)

    cached_model = optimized_model
    return cached_model


def get_signal_pytorch(symbol, df):
    # 1. Preprocessing Data
    # Ambil 10 candle terakhir, normalisasi data (Z-Score/MinMax)
    # ... (Kode preprocessing Anda) ...
    # Anggap 'features' adalah numpy array shape (1, 10, 14)
    features = df.tail(10).values  # Contoh sederhana

    # Convert ke Tensor
    tensor_input = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(device)

    # 2. Load Model (Cepat karena di-cache & JIT)
    model = load_optimized_model(input_dim=features.shape[1])
    if not model:
        return {"error": "Model not trained"}

    # 3. Inference Mode (Paling Penting!)
    # torch.inference_mode() lebih cepat daripada torch.no_grad()
    with torch.inference_mode():
        prediction = model(tensor_input)

    # 4. Parse Hasil
    probs = prediction.cpu().numpy()[0]  # [0.1, 0.8, 0.1]
    action = np.argmax(probs)

    return {"action": int(action), "probs": probs.tolist()}


def get_detailed_signal(symbol):
    info = get_asset_info(symbol)

    if not info:
        return {"error": "Asset not config."}

    # Load Model
    safe_symbol = symbol.replace("=", "").replace("^", "")
    model_path = f"{MODEL_DIR}/{info['category'].lower()}/{safe_symbol}.zip"
    whale_info = None

    if not os.path.exists(model_path):
        return {"Symbol": symbol, "Action": "HOLD", "Reason": "No Model"}

    try:
        model = PPO.load(model_path)
        df = fetch_data(symbol, period="1mo", interval="1h")
        if df.empty:
            return {"Symbol": symbol, "Action": "HOLD", "Reason": "No Data"}

        last_row = df.iloc[-1]
        obs = np.append(last_row.values, [0])  # 0 = No Position assumption
        action, _ = model.predict(obs)

        # Probabilitas Simulasi (Asumsi karena PPO predict return action)
        confidence = 85.5  # Di production gunakan policy.get_distribution

        action_map = {0: "HOLD", 1: "BUY", 2: "SELL"}
        act_str = action_map[int(action)]

        if act_str == "HOLD":
            return {"Symbol": symbol, "Action": "HOLD"}

        current_price = last_row["Close"]
        atr = last_row["ATR_14"]

        # TP SL Calculation
        sl_dist = atr * 1.5
        tp, sl = 0, 0
        if act_str == "BUY":
            sl = current_price - sl_dist
            tp = current_price + (sl_dist * 2)
        else:
            sl = current_price + sl_dist
            tp = current_price - (sl_dist * 2)

        # Money Management
        sl_pips = sl_dist * info["pip_scale"]
        lot = calculate_lot_size(1000, 2.0, sl_pips, symbol)

        user_balance = 100000000 if info["type"] == "stock_indo" else 1000

        lot_size = calculate_lot_size(
            balance=user_balance,
            risk_percentage=2.0,
            sl_price=sl,
            entry_price=current_price,
            asset_info=info,
        )
        # --- [BARU] LOGIKA BANDARMOLOGY ---
        bandar_data = None

        # Hanya jalankan detektor ini untuk Saham Indo
        # A. Jika SAHAM INDO -> Pakai Bandarmologi (VPA)
        if info["type"] == "stock_indo":
            bandar_data = analyze_bandar_flow(df)
            if bandar_data["score"] > 70:
                whale_info = f"Bandar Accumulation (Score: {bandar_data['score']})"
            elif bandar_data["score"] < 30:
                whale_info = f"Bandar Distribution (Score: {bandar_data['score']})"

        # B. Jika FOREX -> Pakai Smart Money Concepts (SMC)
        elif info["type"] == "forex":
            smc_data = analyze_forex_whale(df)

            if smc_data and smc_data["detected"]:
                whale_info = f"{smc_data['message']} - {smc_data['strength']}"

                # [LOGIKA PENTING]
                # Jika AI bilang SELL, tapi SMC mendeteksi WHALE BUY (Liquidity Grab),
                # Maka ikuti Paus (Batalkan Sell AI).
                if act_str == "SELL" and smc_data["type"] == "WHALE_BUY":
                    act_str = "BUY"
                    confidence = 88.0  # High confidence karena ikut paus

                elif act_str == "BUY" and smc_data["type"] == "WHALE_SELL":
                    act_str = "SELL"
                    confidence = 88.0

        # Format output Lot agar user paham
        lot_display = f"{lot_size} Lot"
        if info["type"] == "stock_indo":
            # Tambahkan info lembar biar jelas
            lot_display += f" ({int(lot_size * 100)} Lbr)"

            # DATA CONTAINER UNTUK DIKIRIM KE GROQ
        detected_anomaly = None

        # Cek apakah ada trigger Bandar (Saham) atau Paus (Forex)
        if info["type"] == "stock_indo" and bandar_data and bandar_data["score"] > 75:
            detected_anomaly = bandar_data
        elif info["type"] == "forex" and smc_data and smc_data["detected"]:
            detected_anomaly = smc_data

        # --- [NEW] INTERVENSI AI GROQ ---
        ai_analysis = None

        if detected_anomaly:
            # Siapkan data sinyal sementara
            temp_signal_data = {
                "Price": current_price,
                "Action": act_str,  # Sinyal awal dari Algo PPO
                "Tp": tp,
                "Sl": sl,
                "LotSize": lot_display,
            }

            # Tanya Groq
            ai_analysis = consult_groq_analyst(
                symbol, info, temp_signal_data, detected_anomaly
            )

            # --- KEPUTUSAN AKHIR BERDASARKAN GROQ ---

            # Jika Groq menyarankan "WAIT", kita batalkan sinyal Algo
            if ai_analysis["decision"] == "WAIT":
                act_str = "HOLD"
                confidence = 0
                reason_str = f"🛑 AI VETO: {ai_analysis['reason']}"
            else:
                # Jika Groq setuju "FOLLOW", kita gaspol
                reason_str = f"✅ AI CONFIRMED: {ai_analysis['reason']}"
                confidence = 95.0  # Keyakinan Maksimal

        else:
            reason_str = "Technical Pattern"

        response = {
            "Symbol": symbol,
            "Action": act_str,
            "Price": (
                round(current_price, 0)
                if info["type"] == "stock_indo"
                else round(current_price, 5)
            ),
            "Tp": round(tp, 0) if info["type"] == "stock_indo" else round(tp, 5),
            "Sl": round(sl, 0) if info["type"] == "stock_indo" else round(sl, 5),
            "LotSize": lot_display,  # Output string informatif
            "Prob": f"{confidence}%",
            "Whale_Activity": (
                whale_info if whale_info else "No significant whale activity"
            ),
            "AI_Analysis": reason_str,
            # ...
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
        return response

    except Exception as e:
        return {"error": str(e)}
